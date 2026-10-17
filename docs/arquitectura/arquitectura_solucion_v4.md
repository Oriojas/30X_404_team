# Especificación de Arquitectura v4: Blinka PayAgent (Paybot)

> [!WARNING]
> **Documento histórico.** La arquitectura vigente, con diagramas C4 y el estado real de la implementación, está en [arquitectura_solucion_v5.md](arquitectura_solucion_v5.md).
**Proyecto:** Agentes Autónomos para Pagos Corporativos | **Hackathon 30X**
**Despliegue:** Railway All-in-One PaaS | **Repositorio:** `Oriojas/30X_404_team`

---

## 1. Visión General de la Arquitectura

Siguiendo el consenso técnico entre **Oscar Riojas** y **Luis Felipe Marín Giraldo**, la arquitectura de **Blinka PayAgent** adopta un patrón **Hexagonal (Puertos y Adaptadores)** dentro de un **Monorepo** en GitHub.

Esta arquitectura separa completamente los adaptadores de entrada (Telegram, API REST) y los adaptadores de salida (Gemini, tasas FX, PostgreSQL, notificaciones de Telegram) del **Núcleo de Negocio (Core)**, garantizando que nuevas fuentes de ingesta (como correo electrónico o WhatsApp) se puedan conectar sin modificar las reglas de procesamiento.

```mermaid
flowchart TD
    subgraph System ["ARQUITECTURA HEXAGONAL: BLINKA PAYAGENT"]
        direction TB

        subgraph InAdapters ["ADAPTADORES DE ENTRADA (adapters/inbound)"]
            Telegram["Telegram Webhook (MVP) - Ingesta Fotos/PDF"]
            RestAPI["API REST FastAPI - Dashboard, subida de archivos y decisiones HITL"]
            OtherChannels["Canales Secundarios (Ext) - WhatsApp y Email Webhooks"]
        end

        subgraph Core ["CORE DEL SISTEMA (core/ - Logica de Negocio Pura)"]
            UseCases["Casos de Uso - ProcessInvoice, DecideInvoice, ListInvoices, Get/UpdateRules"]
            FX["FX Engine (Conversion a USD a $0 Markup)"]
            Rules["Motor de Reglas Blinka (Tuberia de Decision en 4 Capas)"]
            Audit["Generador de Explicabilidad (Audit Log Estructurado)"]
            Ports["Puertos de Salida - OCR, FX, Facturas, Reglas, Proveedores, Sanciones, Tesoreria, Notificaciones"]

            UseCases --> FX --> Rules --> Audit
            UseCases --> Ports
        end

        subgraph OutAdapters ["ADAPTADORES DE SALIDA (adapters/outbound)"]
            Gemini["Gemini 1.5 Flash - OCR Multimodal"]
            Rates["Proveedor de Tasas FX"]
            DB[("PostgreSQL (Railway Native) - invoices, company_rules, vendors, sanctions_list, treasury_accounts")]
            TgClient["Cliente API Telegram - Avisos del dictamen"]
        end

        ReactUI["React.js y Tailwind UI - Landing Comercial y Dashboard Stitch"]

        ReactUI -->|"HTTP"| RestAPI
        Telegram -->|"Documento (PDF/Foto)"| UseCases
        RestAPI --> UseCases
        OtherChannels -.->|"Documento"| UseCases
        Ports -.->|"implementa"| Gemini
        Ports -.->|"implementa"| Rates
        Ports -.->|"implementa"| DB
        Ports -.->|"implementa"| TgClient
    end

    style System fill:#f8fafc,stroke:#475569,stroke-width:2px
    style InAdapters fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style OutAdapters fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    style Core fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ReactUI fill:#fefce8,stroke:#ca8a04,stroke-width:2px
```

**Regla de dependencias:** los adaptadores dependen del Core, nunca al revés. El Core solo conoce los puertos; el *composition root* (`backend/app/container.py`) decide qué adaptador concreto implementa cada puerto. Los adaptadores de entrada reciben casos de uso por inyección y nunca importan el contenedor; `backend/tests/test_architecture.py` lo verifica automáticamente.

---

## 2. Estructura del Monorepo (`Oriojas/30X_404_team`)

```text
30X_404_team/
├── backend/                        # API FastAPI & Core Hexagonal
│   ├── app/
│   │   ├── core/                   # Hexágono: lógica de negocio pura
│   │   │   ├── domain/             # models.py, fx_converter.py, rules_pipeline.py, audit_logger.py
│   │   │   ├── ports/              # outbound.py: contratos que implementan los adaptadores
│   │   │   └── use_cases/          # process_invoice.py, query_invoices.py, manage_rules.py
│   │   ├── adapters/
│   │   │   ├── inbound/            # Adaptadores de entrada
│   │   │   │   ├── dependencies.py # Inyección de casos de uso (único punto que ve el contenedor)
│   │   │   │   ├── api/            # Routers REST y DTOs Pydantic
│   │   │   │   └── telegram/       # Webhook de Telegram
│   │   │   └── outbound/           # Adaptadores de salida
│   │   │       ├── ocr/            # Gemini 1.5 Flash
│   │   │       ├── fx/             # Proveedor de tasas de cambio
│   │   │       ├── notifications/  # Router de avisos por canal de origen
│   │   │       ├── db/             # PostgreSQL + schema.sql
│   │   │       └── telegram/       # Cliente API Telegram (notificaciones HITL)
│   │   ├── config.py               # Settings desde el .env raíz
│   │   ├── container.py            # Composition root (inyección de dependencias)
│   │   └── main.py                 # Arranque FastAPI y montaje de routers
│   ├── tests/                      # Pruebas del Core con adaptadores falsos
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                       # Aplicación React + Tailwind CSS
│   ├── src/
│   │   ├── components/             # Dashboard, Audit Table, Rule Controls
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docs/                           # Documentación & Especificaciones
│   ├── arquitectura/arquitectura_solucion_v4.md
│   └── reglas-negocio/reglas_pago_agente_v3.md
├── plan_de_trabajo.md
└── README.md                       # Presentación del proyecto y guías
```

---

## 3. Tubería de Reglas de Negocio & FX Engine

```mermaid
flowchart TD
    Doc["Factura o Cuenta de Cobro (PDF/Imagen)"] --> OCR["Extraccion Multimodal (Gemini 1.5 Flash) - Monto, Moneda, Proveedor, Cuenta"]

    subgraph Pipeline ["Tuberia Determinista en 4 Capas"]
        Capa1["Capa 1: Compliance y SARLAFT (Listas OFAC/ONU y Cuentas Autorizadas)"]
        Capa2["Capa 2: Integridad y Duplicados (Chequeo 30 dias y Confianza OCR > 85%)"]
        Capa3["Capa 3: Solvencia y FX Engine (Normalizacion USD a $0 Markup y Saldo Blinka)"]
        Capa4["Capa 4: Gobierno y Human-in-the-Loop (Umbral $2,000 USD y Proveedor Nuevo)"]

        Capa1 -->|"Pasa"| Capa2
        Capa2 -->|"Pasa"| Capa3
        Capa3 -->|"Pasa"| Capa4
    end

    OCR --> Capa1

    Capa1 -->|"Alerta Critica"| Rejected["REJECTED - Rechazo Automatico"]
    Capa2 -->|"Duplicado"| Rejected
    Capa1 -->|"Cuenta / PEP / NIT"| Scaled
    Capa2 -->|"Tarifa / OCR"| Scaled
    Capa3 -->|"Saldo / Presupuesto"| Scaled["SCALED_TO_HUMAN - Revision humana en el Dashboard"]
    Capa4 -->|"Umbral / Proveedor Nuevo"| Scaled
    Scaled -->|"Operador aprueba o rechaza"| Human["HUMAN_APPROVED / HUMAN_REJECTED"]
    Capa4 -->|"100% Criterios Cumplidos"| Approved["AUTO_APPROVED - Aprobado Autonomamente"]

    style Doc fill:#f8fafc,stroke:#64748b,stroke-width:2px
    style OCR fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style Pipeline fill:#f1f5f9,stroke:#475569,stroke-width:1px
    style Capa1 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa2 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa3 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa4 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Approved fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style Scaled fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style Rejected fill:#fee2e2,stroke:#dc2626,stroke-width:2px
    style Human fill:#e0e7ff,stroke:#4f46e5,stroke-width:2px
```

**Política de recorrido:** un `REJECTED` detiene la tubería de inmediato y las capas siguientes quedan como `NOT_EVALUATED`. Las alertas de escalamiento se acumulan, para que el Audit Log muestre todas las capas y se pueda aplicar HITL-03. El detalle por regla está en [reglas_pago_agente_v3.md](../reglas-negocio/reglas_pago_agente_v3.md).

### Capa 1: Compliance & SARLAFT
- Cotejo automático contra listas restrictivas (OFAC, ONU, GAFI) por razón social, NIT o cuenta bancaria (`sanctions_list`).
- Validación de que la cuenta bancaria de destino pertenezca al beneficiario registrado, condición PEP y consistencia NIT / razón social (`vendors`).
- Se omite si `sarlaft_check_enabled` está desactivado.

### Capa 2: Integridad & Detección de Duplicados
- Detección de facturas duplicadas en la ventana configurada (30 días): mismo proveedor y mismo número **o** mismo monto.
- Monto mayor a la tarifa pactada en contrato (`vendors.contract_amount_usd`).
- Calidad mínima de lectura OCR (≥ 85% de confianza) y campos obligatorios presentes.

### Capa 3: Solvencia & Conversión de Divisas (FX Engine)
- **Extracción de Moneda:** Soporte para facturas en COP, MXN, EUR, BRL, ARS y USD.
- **Normalización FX:** Conversión automática a USD usando la tasa de cambio de referencia.
- **Garantía Blinka:** Transacciones con **$0.00 FX Markup**.
- **Saldo:** Verificación de saldo disponible en la cuenta USD de Blinka (`balance_usd >= usd_amount`) y colchón mínimo de tesorería.
- **Presupuesto:** El acumulado aprobado del mes más la factura no puede superar el presupuesto mensual (`treasury_accounts`).

### Capa 4: Gobierno & Human-in-the-Loop (HITL)
- **Límite Autónomo:** Aprobación automática hasta **$2,000 USD** equivalente.
- **Escalamiento:** Si la factura supera $2,000 USD, es de un proveedor nuevo o acumula 2 o más inconsistencias, queda en `SCALED_TO_HUMAN`.
- **Aprobación humana:** Se hace **solo desde el dashboard** (`POST /api/invoices/{id}/decision`). Telegram y los demás canales son únicamente de ingesta y reciben un aviso con el resultado.

---

## 4. Modelo de Datos PostgreSQL

El DDL completo está en [schema.sql](../../backend/app/adapters/outbound/db/schema.sql) y los datos de demostración en [seed.sql](../../backend/app/adapters/outbound/db/seed.sql). El backend aplica el esquema al arrancar (`DB_AUTO_MIGRATE=true`) y el seed solo si `DB_SEED_DEMO=true`; ambos son idempotentes.

| Tabla | Uso | Capa |
| :--- | :--- | :--- |
| `company_rules` | Umbrales configurables desde el dashboard (límite autónomo, SARLAFT, ventana de duplicados, colchón de tesorería) | Todas |
| `vendors` | Proveedores verificados: NIT, cuenta autorizada, condición PEP, tarifa pactada | 1, 2, 4 |
| `sanctions_list` | Listas restrictivas OFAC / ONU / GAFI | 1 |
| `treasury_accounts` | Saldo USD de la cuenta Blinka y presupuesto mensual | 3 |
| `invoices` | Audit Log: datos de la factura, conversión FX, decisión, explicación, `evaluations` (JSONB por capa) y decisión humana (`decided_by`, `decided_at`, `human_note`) | — |

---

## 5. Despliegue en Railway (All-in-One PaaS)

El proyecto se despliega dentro de un único canvas de Railway:
1. **PostgreSQL Service:** Base de datos relacional administrada.
2. **Backend Service:** FastAPI container ejecutando el webhook de Telegram y la lógica de Gemini.
3. **Frontend Service:** React.js compilado servido con URL pública HTTPS.
4. **Environment Variables:** `DATABASE_URL`, `DB_AUTO_MIGRATE`, `DB_SEED_DEMO`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `GEMINI_API_KEY`.
