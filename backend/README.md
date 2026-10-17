# Blinka PayAgent — Backend API

Servicio backend desarrollado en **Python 3.12** con **FastAPI** bajo **Arquitectura Hexagonal (Puertos y Adaptadores)**. Se encarga de la ingesta de documentos contables, extracción con visión multimodal mediante **Gemini 1.5 Flash**, conversión de divisas con **$0.00 FX Markup**, evaluación en una tubería de 4 capas de negocio y persistencia en **PostgreSQL**.

---

## 🏛️ Arquitectura Hexagonal

El Core no importa FastAPI, Pydantic, SQL ni SDKs externos. Se comunica con el exterior solo a través de **puertos** (`core/ports/`), y los **adaptadores** (`adapters/`) los implementan. `container.py` es el único lugar que elige qué adaptador concreto usar.

```text
backend/app/
├── core/                              # Hexágono: lógica de negocio pura
│   ├── domain/
│   │   ├── models.py                  # Entidades: ExtractedInvoice, CompanyRules, Decision, ProcessedInvoice
│   │   ├── fx_converter.py            # FX Engine: normalización a USD a $0.00 FX Markup
│   │   ├── rules_pipeline.py          # Tubería determinista de 4 capas (Cumplimiento, Integridad, Solvencia, HITL)
│   │   └── audit_logger.py            # Generador de explicabilidad en lenguaje natural
│   ├── ports/
│   │   └── outbound.py                # Contratos: OCRPort, FXRateProvider, InvoiceRepository, RulesRepository, NotificationPort
│   └── use_cases/                     # Puertos de entrada: lo que los adaptadores pueden invocar
│       ├── process_invoice.py         # OCR -> FX -> Reglas -> Audit Log -> Persistencia -> Notificación
│       ├── query_invoices.py          # Historial del Audit Log
│       └── manage_rules.py            # Consultar / actualizar umbrales
├── adapters/
│   ├── inbound/                       # Adaptadores de entrada (driving)
│   │   ├── api/
│   │   │   ├── routers/               # health.py, invoices.py, rules.py
│   │   │   ├── schemas.py             # DTOs Pydantic <-> entidades del dominio
│   │   │   └── dependencies.py        # Inyección de casos de uso en FastAPI
│   │   └── telegram/
│   │       └── webhook.py             # Webhook de Telegram: extrae el adjunto y llama a ProcessInvoice
│   └── outbound/                      # Adaptadores de salida (driven)
│       ├── ocr/gemini_ocr.py          # OCRPort -> Gemini 1.5 Flash
│       ├── fx/static_rates.py         # FXRateProvider -> tasas de referencia
│       ├── db/
│       │   ├── postgres_repository.py # InvoiceRepository y RulesRepository -> PostgreSQL
│       │   └── schema.sql             # DDL inicial de tablas (company_rules, invoices)
│       └── telegram/telegram_client.py# NotificationPort -> API de Telegram (dictamen y botones HITL)
├── config.py                          # Settings (pydantic-settings) leídos del .env raíz
├── container.py                       # Composition root: conecta adaptadores con puertos
└── main.py                            # Arranque FastAPI, CORS y montaje de routers
```

**Regla de dependencias:** `adapters` → `core/use_cases` → `core/domain` + `core/ports`. Nunca al revés.

**Para agregar un canal** (por ejemplo email o WhatsApp), crea un adaptador en `adapters/inbound/` que llame a `ProcessInvoiceUseCase`. **Para cambiar un proveedor** (otro OCR, tasas en vivo), crea una clase que cumpla el puerto y conéctala en `container.py`.

---

## ⚙️ Variables de Entorno

> [!IMPORTANT]
> Siguiendo las reglas del monorepo, **todas las variables de entorno se configuran en el archivo `.env` del directorio raíz**. No se utilizan archivos `.env` locales en `backend/`.

Las variables requeridas para el backend son:
* `PORT`: Puerto de escucha del servicio (por defecto `8000`, inyectado automáticamente en Railway).
* `DATABASE_URL`: URI de conexión a PostgreSQL (`postgresql://db_user:db_password@localhost:5432/db_name`).
* `TELEGRAM_BOT_TOKEN`: Token de autenticación del bot de Telegram.
* `TELEGRAM_WEBHOOK_URL`: URL pública del webhook expuesto para recibir actualizaciones de Telegram.
* `GEMINI_API_KEY`: Clave de API de Google AI Studio para Gemini 1.5 Flash.
* `GEMINI_MODEL`: Modelo a utilizar (por defecto `gemini-1.5-flash`).
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
uvicorn backend.app.main:app --reload --port 8000
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
Las pruebas usan adaptadores falsos, así que no necesitan Gemini, PostgreSQL ni Telegram.

---

## 🐳 Despliegue con Docker (Railway)

El archivo [Dockerfile](Dockerfile) empaqueta la aplicación con Python 3.12-slim:

```bash
docker build -t blinka-backend -f backend/Dockerfile .
docker run -p 8000:8000 --env-file .env blinka-backend
```

En Railway, la variable `$PORT` es asignada en runtime y el contenedor arranca automáticamente con `uvicorn`.

---

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Verificación de estado del servicio |
| `POST` | `/api/webhook/telegram` | Webhook de ingesta para fotos y documentos de Telegram |
| `GET` | `/api/invoices` | Listado histórico de facturas y decisiones del Audit Log (arreglo JSON) |
| `POST` | `/api/invoices` | Creación y evaluación manual de facturas |
| `GET` | `/api/rules` | Consulta de reglas de negocio actuales |
| `POST` | `/api/rules` | Actualización de umbrales autónomos y políticas |

---

## 🔗 Referencias
* [README Principal del Proyecto](../README.md)
* [Frontend (React + Tailwind)](../frontend/README.md)
* [Arquitectura de Solución v4](../docs/arquitectura/arquitectura_solucion_v4.md)
