# Arquitectura de Solución v5: Blinka PayAgent (Paybot)
**Proyecto:** Agentes Autónomos para Pagos Corporativos | **Hackathon 30X — Reto Blinka**
**Estado:** VIGENTE desde el 17 de octubre de 2026 (reemplaza a la [v4](arquitectura_solucion_v4.md)) | **Repositorio:** `Oriojas/30X_404_team`

> Describe la arquitectura **tal como está implementada** en `backend/` y `frontend/`, usando el modelo **C4** (Contexto → Contenedores → Componentes → Código).
> Los principios y el alcance están en [specs/mission.md](../../specs/mission.md), el stack en [specs/tech-stack.md](../../specs/tech-stack.md) y lo pendiente en [specs/roadmap.md](../../specs/roadmap.md).
> Las reglas de negocio detalladas (códigos COMP, INTEG, FIN, HITL) están en [reglas_pago_agente_v3.md](../reglas-negocio/reglas_pago_agente_v3.md).

**Novedades frente a la v4:**
- La aprobación humana ocurre **solo en el dashboard**; los canales (Telegram, web) únicamente ingresan facturas.
- Hexágono explícito: puertos, casos de uso y composition root, con una prueba automática de arquitectura.
- Nuevas tablas para las reglas (`vendors`, `sanctions_list`, `treasury_accounts`), ingesta web y estados `HUMAN_*`.

---

## 1. Nivel 1 — Diagrama de Contexto

Quién usa el sistema y con qué sistemas externos se comunica.

```mermaid
C4Context
    title Contexto del sistema - Blinka PayAgent

    Person(operativo, "Equipo operativo / Proveedor", "Envía facturas en foto o PDF")
    Person(aprobador, "Aprobador financiero", "CFO o tesorería: revisa excepciones y configura reglas")
    Person(auditor, "Auditor / Jurado", "Consulta el Audit Log y prueba el agente")

    System(payagent, "Blinka PayAgent", "Lee, convierte a USD, evalúa con reglas deterministas y explica cada factura")

    System_Ext(telegram, "Telegram", "Bot API: canal de ingesta y avisos")
    System_Ext(gemini, "Google Gemini API", "OCR multimodal: extracción estructurada")

    Rel(operativo, telegram, "Envía foto o PDF")
    Rel(telegram, payagent, "Entrega el update", "Webhook HTTPS")
    Rel(payagent, telegram, "Descarga adjuntos y avisa el dictamen", "Bot API HTTPS")
    Rel(operativo, payagent, "Sube facturas", "Dashboard web")
    Rel(aprobador, payagent, "Aprueba o rechaza escalamientos; ajusta reglas", "Dashboard web")
    Rel(auditor, payagent, "Lee decisiones y explicaciones", "Dashboard web")
    Rel(payagent, gemini, "Envía el documento y recibe JSON", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Fuera del sistema (por alcance del reto):** no se ejecutan pagos reales, no hay conexión con la cuenta bancaria de Blinka (el saldo vive en la tabla `treasury_accounts`) y no hay KYB.

---

## 2. Nivel 2 — Diagrama de Contenedores

Las piezas desplegables y cómo se comunican.

```mermaid
C4Container
    title Contenedores - Blinka PayAgent

    Person(operativo, "Operativo / Proveedor")
    Person(aprobador, "Aprobador financiero")

    System_Ext(telegram, "Telegram Bot API")
    System_Ext(gemini, "Google Gemini API")

    System_Boundary(sys, "Blinka PayAgent") {
        Container(spa, "Dashboard", "React 18, Vite, Tailwind, Nginx", "Landing, Audit Log, aprobación humana, subida de facturas y reglas")
        Container(api, "Backend API", "Python 3.12, FastAPI, asyncpg", "Núcleo hexagonal: OCR, FX, tubería de 4 capas, Audit Log y webhook de Telegram")
        ContainerDb(db, "Base de datos", "PostgreSQL", "invoices, company_rules, vendors, sanctions_list, treasury_accounts")
    }

    Rel(operativo, telegram, "Foto o PDF")
    Rel(aprobador, spa, "Usa", "HTTPS")
    Rel(operativo, spa, "Sube facturas", "HTTPS")
    Rel(spa, api, "Llama a la API REST", "JSON / HTTPS")
    Rel(telegram, api, "POST /api/webhook/telegram", "HTTPS + secret token")
    Rel(api, telegram, "getFile, sendMessage", "HTTPS")
    Rel(api, gemini, "Extracción OCR", "HTTPS")
    Rel(api, db, "Lee y escribe", "SQL / asyncpg")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

| Contenedor | Tecnología | Responsabilidad | Código |
| :--- | :--- | :--- | :--- |
| **Dashboard** | React 18 + Vite + Tailwind, servido con Nginx | UI del equipo financiero; consume la API en `VITE_API_BASE_URL` | `frontend/` |
| **Backend API** | FastAPI + asyncpg + httpx | Toda la lógica del agente y los canales de ingesta | `backend/app/` |
| **Base de datos** | PostgreSQL (Railway native; probado con 16) | Reglas, datos de referencia y Audit Log | `backend/app/adapters/outbound/db/schema.sql` |

---

## 3. Nivel 3 — Diagrama de Componentes del Backend (Hexágono)

```mermaid
C4Component
    title Componentes - Backend API (arquitectura hexagonal)

    Container(spa, "Dashboard", "React")
    System_Ext(telegram, "Telegram Bot API")
    System_Ext(gemini, "Google Gemini API")
    ContainerDb(db, "PostgreSQL")

    Container_Boundary(api, "Backend API") {
        Boundary(inbound, "Adaptadores de entrada") {
            Component(rest, "API REST", "FastAPI routers", "invoices, rules, health")
            Component(webhook, "Webhook Telegram", "FastAPI router", "Valida el secret token y extrae el adjunto")
        }
        Boundary(core, "Core") {
            Component(usecases, "Casos de uso", "Python", "ProcessInvoice, DecideInvoice, ListInvoices, Get/UpdateRules")
            Component(domain, "Dominio", "Python puro", "RulesPipeline, FXConverter, AuditLogger, entidades")
            Component(ports, "Puertos", "typing.Protocol", "OCR, FX, Facturas, Reglas, Proveedores, Sanciones, Tesorería, Notificaciones")
        }
        Boundary(outbound, "Adaptadores de salida") {
            Component(ocr, "GeminiOCRAdapter", "SDK Gemini", "Implementa OCRPort")
            Component(repos, "Repositorios Postgres", "asyncpg", "Implementan los puertos de datos")
            Component(notify, "Notificaciones", "ChannelNotificationRouter + TelegramClient", "Avisa al canal de origen")
            Component(fx, "StaticFXRateProvider", "Python", "Tasas de referencia")
        }
    }

    Rel(spa, rest, "JSON / HTTPS")
    Rel(telegram, webhook, "Update")
    Rel(rest, usecases, "Invoca")
    Rel(webhook, usecases, "Invoca")
    Rel(usecases, domain, "Usa")
    Rel(usecases, ports, "Depende de")
    Rel(ocr, gemini, "HTTPS")
    Rel(repos, db, "SQL")
    Rel(notify, telegram, "sendMessage")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Los adaptadores de salida **implementan** los puertos; el Core nunca los importa. `container.py` (composition root) crea cada adaptador y lo inyecta en los casos de uso. Los routers reciben los casos de uso con `adapters/inbound/dependencies.py`, el único punto de los adaptadores que ve el contenedor.

### Regla de dependencias (verificada por `backend/tests/test_architecture.py`)

| Capa | Puede importar | No puede importar |
| :--- | :--- | :--- |
| `core/domain` | Librería estándar, `core/domain` | Puertos, casos de uso, frameworks, adaptadores |
| `core/ports` | `core/domain` | Casos de uso, frameworks, adaptadores |
| `core/use_cases` | `core/domain`, `core/ports` | Frameworks, adaptadores |
| `adapters/inbound` | Core, FastAPI | Adaptadores de salida, `container`, `config`, `main` |
| `adapters/outbound` | Core, SDKs (asyncpg, httpx, Gemini) | Adaptadores de entrada, `container`, `config`, `main` |
| `container.py` / `main.py` | Todo | — |

Además, todos los imports son absolutos desde `app` y el Core solo depende de la librería estándar.

---

## 4. Nivel 4 — Código

| Ruta (`backend/app/`) | Contenido |
| :--- | :--- |
| `core/domain/models.py` | Entidades: `ExtractedInvoice`, `Vendor`, `TreasuryStatus`, `CompanyRules`, `Decision`, `ProcessedInvoice`, `DecisionStatus` |
| `core/domain/rules_pipeline.py` | Tubería determinista de 4 capas y generación de la explicación |
| `core/domain/fx_converter.py` | Conversión pura a USD ($0.00 markup) |
| `core/domain/audit_logger.py` | Construye el registro del Audit Log |
| `core/domain/errors.py` | `InvoiceNotFoundError`, `InvalidDecisionStateError` |
| `core/ports/outbound.py` | Contratos de los adaptadores de salida |
| `core/use_cases/` | `process_invoice.py`, `decide_invoice.py`, `query_invoices.py`, `manage_rules.py` |
| `adapters/inbound/api/` | Routers REST (`routers/`) y DTOs Pydantic (`schemas.py`) |
| `adapters/inbound/telegram/webhook.py` | Webhook con su propio puerto `TelegramFileSource` |
| `adapters/outbound/db/` | `postgres_repository.py`, `schema.sql`, `seed.sql` |
| `adapters/outbound/ocr/gemini_ocr.py` | Adaptador OCR (**stub** hasta la Fase 1 del roadmap) |
| `adapters/outbound/fx/static_rates.py` | Tasas fijas; `None` si la moneda no está soportada |
| `adapters/outbound/notifications/channel_router.py` | Enruta avisos por canal de origen |
| `adapters/outbound/telegram/telegram_client.py` | `getFile`, descarga de adjuntos y `sendMessage` |
| `config.py` · `container.py` · `main.py` | Settings, composition root, arranque y manejo de errores |

---

## 5. Vista Dinámica — Flujo de una Factura

### 5.1 Ingesta por Telegram

```mermaid
sequenceDiagram
    autonumber
    actor U as Operativo
    participant T as Telegram
    participant W as Webhook (inbound)
    participant P as ProcessInvoice (caso de uso)
    participant O as Gemini (OCR)
    participant D as PostgreSQL
    participant R as RulesPipeline (dominio)

    U->>T: Envía foto o PDF
    T->>W: POST /api/webhook/telegram + secret token
    W->>W: Valida el secret token (401 / 503)
    W->>T: getFile y descarga del adjunto
    W->>P: from_document(bytes, mime, TELEGRAM, chat_id)
    P-->>T: Aviso "Factura recibida"
    P->>O: extract_invoice_data
    O-->>P: ExtractedInvoice
    P->>P: Conversión a USD (tasa del FXRateProvider)
    par Consultas en paralelo
        P->>D: Proveedor, sanciones, tesorería, gasto del mes
    end
    par
        P->>D: ¿Duplicado? ¿Historial de pagos?
    end
    P->>R: evaluate_invoice(factura, contexto, reglas)
    R-->>P: Decision (estado, alertas, explicación)
    P->>D: INSERT en invoices (Audit Log)
    P-->>T: Aviso del dictamen (sin botones)
    W-->>T: 200 {"status": "processed"}
```

La **subida web** (`POST /api/invoices/upload`) sigue el mismo camino desde el paso 5, con canal `WEB` y sin avisos. `POST /api/invoices` entra directo en `from_extracted`, sin OCR.

### 5.2 Decisión humana en el dashboard

```mermaid
sequenceDiagram
    autonumber
    actor A as Aprobador
    participant S as Dashboard
    participant API as API REST
    participant C as DecideInvoice (caso de uso)
    participant D as PostgreSQL
    participant N as ChannelNotificationRouter

    A->>S: Aprueba o rechaza una factura SCALED_TO_HUMAN
    S->>API: POST /api/invoices/{id}/decision
    API->>C: execute(id, decisión, decided_by, nota)
    C->>D: UPDATE ... WHERE id = ? AND decision_status = 'SCALED_TO_HUMAN'
    alt La factura seguía escalada
        D-->>C: Fila actualizada (HUMAN_APPROVED / HUMAN_REJECTED)
        C->>N: notify_decision
        N-->>N: Avisa solo si el canal de origen tiene notificador
        API-->>S: 200 con la factura actualizada
    else Otro operador decidió antes, o no estaba escalada
        API-->>S: 409 Conflict
    end
```

---

## 6. Tubería Determinista de 4 Capas

```mermaid
flowchart TD
    In["Factura extraída + conversión a USD"] --> C1

    C1["Capa 1: Compliance y SARLAFT - COMP-01 a COMP-04"] -->|"Pasa o escala"| C2
    C2["Capa 2: Integridad - INTEG-01 a INTEG-04"] -->|"Pasa o escala"| C3
    C3["Capa 3: Solvencia - FIN-01 a FIN-03"] -->|"Pasa o escala"| C4
    C4["Capa 4: Gobierno HITL - HITL-01 a HITL-03"] --> Dec{"¿Alertas acumuladas?"}

    C1 -->|"COMP-01: lista restrictiva"| Rej["REJECTED"]
    C2 -->|"INTEG-01: duplicado"| Rej
    Dec -->|"Ninguna"| Auto["AUTO_APPROVED"]
    Dec -->|"Una o más"| Scaled["SCALED_TO_HUMAN"]
    Scaled -->|"Decisión en el dashboard"| Human["HUMAN_APPROVED / HUMAN_REJECTED"]

    style Auto fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style Scaled fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style Rej fill:#fee2e2,stroke:#dc2626,stroke-width:2px
    style Human fill:#e0e7ff,stroke:#4f46e5,stroke-width:2px
```

- **Un `REJECTED` corta** la evaluación: las capas siguientes quedan `NOT_EVALUATED`.
- **Las alertas de escalamiento se acumulan**, para registrar todas las capas y poder aplicar HITL-03.
- Con `sarlaft_check_enabled = false`, la Capa 1 queda `SKIPPED`. Con moneda no soportada (INTEG-04), la Capa 3 también queda `SKIPPED`.
- Cada capa se guarda en `invoices.evaluations` (JSONB) con su estado (`PASSED`, `TRIGGERED`, `SKIPPED`, `NOT_EVALUATED`) y sus alertas.

---

## 7. Modelo de Datos

```mermaid
erDiagram
    company_rules {
        varchar company_id UK
        numeric max_autonomous_usd
        boolean sarlaft_check_enabled
        int duplicate_check_days
        numeric min_treasury_buffer_usd
    }
    treasury_accounts {
        varchar company_id UK
        numeric balance_usd
        numeric monthly_budget_usd
    }
    vendors {
        varchar tax_id UK
        varchar legal_name
        varchar bank_account
        boolean is_pep
        numeric contract_amount_usd
    }
    sanctions_list {
        varchar list_source
        varchar entity_name
        varchar tax_id
        varchar bank_account
    }
    invoices {
        serial id PK
        varchar invoice_number
        varchar vendor_name
        varchar vendor_tax_id
        numeric original_amount
        varchar original_currency
        numeric fx_rate_applied
        numeric usd_amount
        varchar channel_source
        bigint source_chat_id
        varchar decision_status
        text audit_explanation
        jsonb evaluations
        varchar decided_by
        timestamp decided_at
    }
    company_rules ||--|| treasury_accounts : "company_id"
    vendors ||--o{ invoices : "tax_id = vendor_tax_id"
```

La relación entre `vendors` e `invoices` es **lógica** (por NIT o razón social), no una clave foránea: una factura puede ser de un proveedor que todavía no está en el registro (HITL-02). El DDL completo está en [schema.sql](../../backend/app/adapters/outbound/db/schema.sql) y los datos ficticios en [seed.sql](../../backend/app/adapters/outbound/db/seed.sql).

---

## 8. API REST

| Método | Ruta | Uso |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Estado del servicio y de la conexión a PostgreSQL |
| `GET` | `/api/invoices` | Audit Log (arreglo JSON, con `evaluations` por capa) |
| `POST` | `/api/invoices` | Evaluar una factura con datos estructurados (sin OCR) |
| `POST` | `/api/invoices/upload` | Ingesta web: JPG, PNG, WEBP o PDF, máx. 10 MB |
| `POST` | `/api/invoices/{id}/decision` | Decisión humana (`404` / `409`) |
| `GET` / `POST` | `/api/rules` | Consultar o actualizar umbrales |
| `POST` | `/api/webhook/telegram` | Ingesta por Telegram (`401` sin token válido, `503` sin secret configurado) |

---

## 9. Despliegue (Railway)

```mermaid
C4Deployment
    title Despliegue - Railway (un solo proyecto)

    Deployment_Node(railway, "Railway", "PaaS") {
        Deployment_Node(fe, "Servicio Frontend", "Docker: node:20-alpine build + Nginx") {
            Container(spa, "Dashboard", "React SPA estática")
        }
        Deployment_Node(be, "Servicio Backend", "Docker: python:3.12-slim + uvicorn") {
            Container(api, "Backend API", "FastAPI")
        }
        Deployment_Node(pg, "PostgreSQL", "Railway native") {
            ContainerDb(db, "Base de datos", "PostgreSQL")
        }
    }

    Rel(spa, api, "HTTPS", "VITE_API_BASE_URL")
    Rel(api, db, "asyncpg", "DATABASE_URL")
```

| Variable | Servicio | Uso |
| :--- | :--- | :--- |
| `DATABASE_URL` | Backend | Conexión a PostgreSQL. Sin ella, los endpoints de datos responden `503` |
| `DB_AUTO_MIGRATE` / `DB_SEED_DEMO` | Backend | Aplicar `schema.sql` / cargar datos ficticios de demo |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Backend | OCR |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_WEBHOOK_SECRET` | Backend | Canal Telegram (registrar `setWebhook` con `secret_token`) |
| `ALLOWED_ORIGINS` | Backend | CORS: URL del dashboard |
| `VITE_API_BASE_URL` | Frontend | URL pública del backend |

El backend aplica el esquema al arrancar, así que no hace falta ejecutar el DDL a mano. El paso a paso está en la Fase 4 del [roadmap](../../specs/roadmap.md).

---

## 10. Seguridad y Fallas Seguras

| Riesgo | Mitigación implementada |
| :--- | :--- |
| Aprobar un pago indebido | Reglas deterministas; la IA solo extrae datos. Sin datos de tesorería se asume saldo 0, y toda factura escala |
| Moneda desconocida o mal leída | Nunca se convierte 1:1: escala por INTEG-04 |
| OCR fallido o ilegible | Extracción vacía con confianza 0: escala por INTEG-03 |
| Llamadas falsas al webhook | Secret token de Telegram comparado en tiempo constante; sin secret configurado, el webhook responde 503 |
| Dos operadores deciden a la vez | `UPDATE` condicionado al estado `SCALED_TO_HUMAN`: solo gana uno, el otro recibe 409 |
| Datos ficticios en producción | El seed solo se carga con `DB_SEED_DEMO=true` |
| Falla al notificar | Se registra en el log y no revierte la decisión ya guardada |

---

## 11. Decisiones de Arquitectura

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| 1 | Arquitectura hexagonal con prueba automática | Sumar canales (email, WhatsApp) o cambiar proveedores sin tocar las reglas |
| 2 | La IA solo extrae; las reglas deciden | Reproducibilidad, auditoría y tolerancia cero |
| 3 | Los canales solo ingresan facturas; la aprobación ocurre en el dashboard | Separar a quien envía de quien autoriza, y registrar quién decide |
| 4 | Estados `HUMAN_*` separados de `AUTO_*` | Medir la autonomía real del agente |
| 5 | SQL explícito con asyncpg (sin ORM) | Pocas tablas, consultas simples y control total de la idempotencia del esquema |
| 6 | Tasas FX fijas | Demo reproducible; reemplazables por un proveedor en vivo vía `FXRateProvider` |
| 7 | SDK `google-genai` para Gemini | SDK oficial vigente; `google-generativeai` está deprecado |
| 8 | Esquema migrado al arrancar; seed opcional | Despliegue en Railway sin pasos manuales, sin datos ficticios por defecto |

---

## 12. Estado de Implementación

| Pieza | Estado |
| :--- | :--- |
| Hexágono, tubería de 4 capas, Audit Log, decisión humana, API REST | ✅ Implementado y probado (incluida la integración con PostgreSQL) |
| Webhook de Telegram (secret token, descarga y avisos) | ✅ Implementado; sin probar contra la API real de Telegram |
| OCR con Gemini | ⏳ Stub — Fase 1 del roadmap |
| Ingesta idempotente por canal | ⏳ Fase 2 |
| Dashboard conectado a la API real | ⏳ Fase 3 |
| Despliegue en Railway con estas variables | ⏳ Fase 4 |
