# Blinka PayAgent — Backend API

Servicio backend desarrollado en **Python 3.12** con **FastAPI** bajo **Arquitectura Hexagonal (Puertos y Adaptadores)**. Se encarga de la ingesta de documentos contables, extracción con visión multimodal mediante **Gemini Flash** (SDK `google-genai`), conversión de divisas con **$0.00 FX Markup**, evaluación en una tubería de 4 capas de negocio y persistencia en **PostgreSQL**.

---

## 🏛️ Arquitectura Hexagonal

El Core no importa FastAPI, Pydantic, SQL ni SDKs externos. Se comunica con el exterior solo a través de **puertos** (`core/ports/`), y los **adaptadores** (`adapters/`) los implementan. `container.py` es el único lugar que elige qué adaptador concreto usar.

```text
backend/app/
├── core/                              # Hexágono: lógica de negocio pura
│   ├── domain/
│   │   ├── models.py                  # Entidades: ExtractedInvoice, Vendor, TreasuryStatus, Decision, ProcessedInvoice
│   │   ├── errors.py                  # Errores de negocio (factura inexistente, estado no decidible)
│   │   ├── fx_converter.py            # FX Engine: normalización a USD a $0.00 FX Markup
│   │   ├── rules_pipeline.py          # Tubería determinista de 4 capas (Cumplimiento, Integridad, Solvencia, HITL)
│   │   └── audit_logger.py            # Generador de explicabilidad en lenguaje natural
│   ├── ports/
│   │   └── outbound.py                # Contratos: OCRPort, FXRateProvider, InvoiceRepository, RulesRepository,
│   │                                  #            VendorRepository, SanctionsRepository, TreasuryRepository, NotificationPort
│   └── use_cases/                     # Puertos de entrada: lo que los adaptadores pueden invocar
│       ├── process_invoice.py         # OCR -> FX -> Reglas -> Audit Log -> Persistencia -> Notificación
│       ├── decide_invoice.py          # Aprobación / rechazo humano desde el dashboard
│       ├── query_invoices.py          # Historial del Audit Log
│       └── manage_rules.py            # Consultar / actualizar umbrales
├── adapters/
│   ├── inbound/                       # Adaptadores de entrada (driving)
│   │   ├── dependencies.py            # Entrega casos de uso a los routers (único punto que ve el contenedor)
│   │   ├── api/
│   │   │   ├── routers/               # health.py, invoices.py, rules.py
│   │   │   └── schemas.py             # DTOs Pydantic <-> entidades del dominio
│   │   └── telegram/
│   │       └── webhook.py             # Webhook de Telegram: extrae el adjunto y llama a ProcessInvoice
│   └── outbound/                      # Adaptadores de salida (driven)
│       ├── ocr/gemini_ocr.py          # OCRPort -> Gemini Flash (google-genai)
│       ├── fx/static_rates.py         # FXRateProvider -> tasas de referencia (None si la moneda no está soportada)
│       ├── notifications/channel_router.py # NotificationPort -> enruta el aviso al canal de origen
│       ├── db/
│       │   ├── postgres_repository.py # Repositorios -> PostgreSQL (asyncpg)
│       │   ├── schema.sql             # DDL idempotente de todas las tablas
│       │   └── seed.sql               # Datos de demostración para la Test Suite TC-01..TC-07
│       └── telegram/telegram_client.py# Notificador del canal TELEGRAM y descarga de adjuntos
├── config.py                          # Settings (pydantic-settings) leídos del .env raíz
├── container.py                       # Composition root: conecta adaptadores con puertos
└── main.py                            # Arranque FastAPI, CORS y montaje de routers
```

**Regla de dependencias:** `adapters` → `core/use_cases` → `core/domain` + `core/ports`. Nunca al revés.

* El Core solo importa la librería estándar y a sí mismo.
* Los routers reciben **casos de uso** por inyección (`adapters/inbound/dependencies.py`); ningún adaptador importa `container.py`, `config.py` ni `main.py`.
* Los adaptadores de salida no importan adaptadores de entrada.
* Todos los imports son absolutos desde `app` (`from app.core.domain.models import ...`). Por eso `uvicorn` se ejecuta desde `backend/` o con `--app-dir backend`.

`tests/test_architecture.py` verifica estas reglas en cada `pytest`.

**Para agregar un canal** (por ejemplo email o WhatsApp), crea un adaptador en `adapters/inbound/` que llame a `ProcessInvoiceUseCase`. **Para cambiar un proveedor** (otro OCR, tasas en vivo), crea una clase que cumpla el puerto y conéctala en `container.py`.

---

## ⚙️ Variables de Entorno

> [!IMPORTANT]
> Siguiendo las reglas del monorepo, **todas las variables de entorno se configuran en el archivo `.env` del directorio raíz**. No se utilizan archivos `.env` locales en `backend/`.

Las variables requeridas para el backend son:
* `PORT`: Puerto de escucha del servicio (por defecto `8000`, inyectado automáticamente en Railway).
* `DATABASE_URL`: URI de conexión a PostgreSQL (`postgresql://db_user:db_password@localhost:5432/db_name`). Sin ella el servicio arranca, pero los endpoints de datos responden `503`.
* `DB_AUTO_MIGRATE`: Si es `true` (por defecto), al arrancar aplica `schema.sql` (idempotente).
* `DB_SEED_DEMO`: Si es `true`, carga `seed.sql` con proveedores, listas restrictivas y tesorería **ficticios** para la demo. Por defecto es `false`; actívalo solo en entornos de demostración.
* `TELEGRAM_BOT_TOKEN`: Token de autenticación del bot de Telegram.
* `TELEGRAM_WEBHOOK_URL`: URL pública del webhook expuesto para recibir actualizaciones de Telegram.
* `TELEGRAM_WEBHOOK_SECRET`: Secreto que Telegram envía en el header `X-Telegram-Bot-Api-Secret-Token`. Sin él el webhook responde `503` (falla cerrado); con un token distinto responde `401`.
* `GEMINI_API_KEY`: Clave de API de Google AI Studio. Sin ella el OCR devuelve una extracción vacía y toda factura por archivo escala por `INTEG-03`.
* `GEMINI_MODEL`: Modelo a utilizar (por defecto `gemini-3.8-flash`, el Flash estable vigente).
* `ALLOWED_ORIGINS`: Orígenes CORS permitidos, separados por coma (por defecto `*`).
* `COMPANY_ID`, `MAX_AUTONOMOUS_USD`, `SARLAFT_CHECK_ENABLED`, `DUPLICATE_CHECK_DAYS`: Reglas por defecto mientras no se lean de `company_rules`.

Consulta la plantilla completa en [.env.example](../.env.example).

---

## 🚀 Ejecución Local

### 1. Crear y activar entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Iniciar el servidor de desarrollo
Desde el directorio raíz:
```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```
O desde la carpeta `backend/`:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

La documentación interactiva Swagger estará disponible en `http://localhost:8000/docs`.

### 4. Ejecutar las pruebas
Desde la carpeta `backend/`:
```bash
pytest
```
Las pruebas unitarias usan adaptadores falsos, así que no necesitan Gemini, PostgreSQL ni Telegram.

La prueba de integración corre la Test Suite TC-01..TC-07 contra un PostgreSQL real con el seed. Usa una base desechable, porque la prueba borra y recrea las tablas:
```bash
docker run -d --rm --name blinka-pg-test -e POSTGRES_USER=blinka -e POSTGRES_PASSWORD=blinka -e POSTGRES_DB=blinka_test -p 54329:5432 postgres:16-alpine
TEST_DATABASE_URL=postgresql://blinka:blinka@localhost:54329/blinka_test pytest
```

---

## 🐳 Docker

El archivo [Dockerfile](Dockerfile) empaqueta la aplicación con Python 3.12-slim. [.dockerignore](.dockerignore) deja fuera `tests/` y `scripts/`.

```bash
docker build -t blinka-backend backend
docker run -p 8000:8000 --env-file .env blinka-backend
```

El contenedor escucha en `$PORT`, que Railway asigna al arrancar.

---

## ☁️ Despliegue en Railway

La infraestructura está declarada como código en [.railway/railway.ts](../.railway/railway.ts). Railway deprecó `railway.json` y `railway.toml` (Config as Code), y desde el 28-ago-2026 no se pueden activar en servicios nuevos.

| Servicio | Origen | Healthcheck | Variables |
| :--- | :--- | :--- | :--- |
| `Postgres` | Plantilla de Railway | — | La plantilla genera `DATABASE_URL`. |
| `backend` | `/backend`, rama `master`, `Dockerfile` | `/api/health`, 120 s | `DATABASE_URL` toma la referencia de `Postgres`. `DB_AUTO_MIGRATE` y `DB_SEED_DEMO` valen `true`. `ENVIRONMENT=production`. `ALLOWED_ORIGINS` apunta al dominio del frontend y `TELEGRAM_WEBHOOK_URL` al dominio propio + `/api/webhook/telegram`. Secretos con `preserve()`. |
| `30X_404_team` (frontend) | `/frontend`, rama `master`, `Dockerfile` | `/`, 60 s | `VITE_API_BASE_URL` apunta al dominio del `backend`. |

Los dominios se resuelven con referencias de Railway (`${{backend.RAILWAY_PUBLIC_DOMAIN}}`), así que no hay URLs escritas a mano. Los dos servicios se vuelven a desplegar solos con cada push a `master`. Hoy el backend está en `https://backend-production-ea088.up.railway.app` y el dashboard en `https://30x404team-production.up.railway.app`.

### Primer despliegue o cambios de infraestructura

Desde la raíz del repo:

```bash
brew install railway        # Railway CLI (probado con 5.70.0)
npm install                 # SDK `railway` fijado en el package.json de la raíz
railway login
railway link                # proyecto 30x404team, entorno production
railway config plan         # muestra cambios sin aplicarlos; revisa que no destruya nada
railway config apply
railway domain --service backend   # solo la primera vez: genera el dominio público
```

Un `apply` de proyecto completo **borra lo que no esté en el archivo**: todo servicio nuevo se agrega primero a `railway.ts`. Después de aplicar, `railway config plan` debe responder "already up to date".

### Secretos

Nunca van al repo ni a `railway.ts`, donde figuran como `preserve()`. Se cargan una vez y se mantienen entre `apply`:

```bash
railway variables --service backend --set "GEMINI_API_KEY=..."
railway variables --service backend --set "TELEGRAM_BOT_TOKEN=..."
railway variables --service backend --set "TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32)"
```

### Webhook de Telegram

Con las variables de producción, sin copiarlas al `.env` local:

```bash
cd backend
railway run --service backend -- python -m scripts.registrar_webhook          # setWebhook + getWebhookInfo
railway run --service backend -- python -m scripts.registrar_webhook --info   # solo consultar
railway run --service backend -- python -m scripts.registrar_webhook --borrar # volver a probar en local
```

El script nunca imprime el token. Si `TELEGRAM_WEBHOOK_SECRET` cambia, hay que volver a registrar el webhook.

### Prueba de humo

Verifica `/api/health`, TC-01..TC-07, `/api/rules` y el CORS del frontend. Cada caso usa un `Idempotency-Key` fijo, así que se puede repetir sin crear duplicados. Ojo: desde la segunda corrida los casos responden `200` con la factura guardada (el script lo advierte), así que solo la primera corrida sobre una base recién sembrada evalúa el deploy actual. Las facturas del humo quedan en la base y se ven en el dashboard. Los casos viven en `scripts/casos_demo.py`, compartidos con `tests/test_postgres_integration.py`:

```bash
cd backend
python -m scripts.humo_produccion https://backend-production-ea088.up.railway.app \
  --origen https://30x404team-production.up.railway.app
```

Sale con código `1` si algún caso falla. Supone el seed de demostración y las reglas por defecto: si alguien cambió los umbrales desde el dashboard, TC-04 y TC-05 pueden variar.

---

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Estado del servicio y de la conexión a PostgreSQL |
| `POST` | `/api/webhook/telegram` | Canal de ingesta: fotos y documentos de Telegram. Un `update_id` ya procesado responde `200 {"status": "duplicate"}`; uno aún en proceso, `503` |
| `GET` | `/api/invoices` | Listado histórico de facturas y decisiones del Audit Log (arreglo JSON, con `evaluations` por capa) |
| `POST` | `/api/invoices` | Evaluación de una factura con datos ya estructurados (sin OCR). Acepta `Idempotency-Key` |
| `POST` | `/api/invoices/upload` | Canal de ingesta web: `multipart/form-data` con campo `file` (JPG, PNG, WEBP o PDF, máx. 10 MB). Acepta `Idempotency-Key` |
| `POST` | `/api/invoices/{id}/decision` | Decisión humana sobre una factura `SCALED_TO_HUMAN`: `{"decision": "APPROVE" \| "REJECT", "decided_by": "...", "note": "..."}`. Responde `404` si no existe y `409` si no está escalada |
| `GET` | `/api/rules` | Consulta de reglas de negocio actuales |
| `POST` | `/api/rules` | Actualización de umbrales autónomos y políticas |
| `GET` | `/api/treasury` | Saldo, presupuesto mensual y gasto aprobado del mes de la cuenta Blinka |

### Ingesta idempotente

Una misma entrega se procesa una sola vez por canal, aunque llegue repetida:

| Canal | Identificador de la entrega | Primera vez | Repetida | Aún en proceso |
| :--- | :--- | :--- | :--- | :--- |
| `POST /api/invoices/upload` | Header `Idempotency-Key` | `201` | `200` con la misma factura | `409` (reintenta con la misma clave) |
| `POST /api/invoices` | Header `Idempotency-Key` | `201` | `200` con la misma factura | `409` |
| Webhook de Telegram | `update_id` | `{"status": "processed", ...}` | `200 {"status": "duplicate", "decision": ...}` | `503` (Telegram reintenta más tarde) |

- El header es opcional (1 a 200 caracteres; si no, `422`). Sin él, cada solicitud crea una factura nueva.
- Una repetición no reprocesa ni vuelve a avisar al canal; Telegram tampoco vuelve a descargar el archivo.
- Si el procesamiento falla, la clave se libera y el reintento sí procesa. Un reclamo que queda colgado más de 5 minutos (p. ej. por un reinicio) se puede retomar.
- La clave es por canal: la misma clave en `/upload` y en `/api/invoices` son entregas distintas.

```bash
curl -s -X POST localhost:8000/api/invoices/upload -H "Idempotency-Key: $(uuidgen)" -F "file=@tests/fixtures/factura_devstudio.png"
```

---

## 🤖 Registrar el Webhook de Telegram

Registra la URL con el mismo secreto configurado en `TELEGRAM_WEBHOOK_SECRET`:
```bash
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" -d "url=$TELEGRAM_WEBHOOK_URL" -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

---

## 🔄 Flujo de una Factura

1. **Ingesta:** Telegram, la subida web o la carga por API entregan la factura a `ProcessInvoiceUseCase`. Los canales **solo ingresan facturas**: no aprueban. Cada entrega se reclama en `ingested_messages` para procesarse una sola vez (ver *Ingesta idempotente*).
2. **OCR y FX:** se calcula el SHA-256 del archivo; si es idéntico a una factura vigente de la ventana de duplicados, no se llama al OCR y la factura se rechaza por `INTEG-01` citando la original. Si no, Gemini extrae los datos y el FX Engine convierte a USD con tasas fijas y $0.00 de markup. Una moneda no soportada nunca se convierte 1:1: la factura escala por `INTEG-04`.
3. **Tubería de 4 capas:** consulta proveedores, listas restrictivas, tesorería e historial en PostgreSQL. Un `REJECTED` detiene la evaluación; las alertas de escalamiento se acumulan.
4. **Audit Log:** se guarda la decisión con la explicación y el detalle de cada capa (`evaluations`), y el `ChannelNotificationRouter` avisa solo al canal de origen.
5. **Decisión humana:** las facturas en `SCALED_TO_HUMAN` se aprueban o rechazan **solo desde el dashboard** y quedan como `HUMAN_APPROVED` o `HUMAN_REJECTED`, con quién decidió y cuándo. La actualización es atómica: si dos operadores deciden a la vez, solo gana uno y el otro recibe `409`.

**Estados:** `AUTO_APPROVED`, `SCALED_TO_HUMAN`, `REJECTED`, `HUMAN_APPROVED`, `HUMAN_REJECTED`.

> **OCR:** Gemini devuelve los datos ya normalizados (monto numérico, moneda ISO 4217 deducida del documento, fecha ISO) y el adaptador solo convierte tipos. Si la moneda es ambigua queda como `XXX` y la factura escala por `INTEG-04`; los campos faltantes o la confianza menor a 0.85 escalan por `INTEG-03`. Ante cualquier falla (sin key, error de red, JSON inválido) la extracción queda vacía con confianza 0 y la factura escala: nunca se aprueba por defecto. Hay facturas ficticias de prueba en [`tests/fixtures`](tests/fixtures/README.md).

---

## 🔗 Referencias
* [README Principal del Proyecto](../README.md)
* [Frontend (React + Tailwind)](../frontend/README.md)
* [Arquitectura de Solución v5 (C4)](../docs/arquitectura/arquitectura_solucion_v5.md)
