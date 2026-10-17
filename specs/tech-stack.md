# Stack Tecnológico — Blinka PayAgent (Paybot)

> Parte de la constitución del proyecto, junto con [mission.md](mission.md) y [roadmap.md](roadmap.md).
> Agregar, cambiar o quitar una tecnología de esta lista es una decisión explícita: se actualiza este documento en el mismo cambio.

## Resumen

| Capa | Tecnología | Estado |
| :--- | :--- | :--- |
| Backend | Python 3.12 + FastAPI | En uso |
| Validación y configuración | Pydantic v2 + pydantic-settings | En uso |
| Base de datos | PostgreSQL (Railway native; probado con 16) + asyncpg | En uso |
| OCR / visión | Google Gemini (`gemini-3.8-flash`) vía SDK **`google-genai`** | En uso |
| Canal de ingesta | Telegram Bot API vía `httpx` | En uso |
| Frontend | React 18 + Vite 5 + Tailwind CSS 3 + lucide-react | En uso |
| Contenedores | Docker: `python:3.12-slim` (backend), `node:20-alpine` + Nginx (frontend) | En uso |
| Despliegue | Railway (PostgreSQL + backend + frontend en un solo canvas), infraestructura en `.railway/railway.ts` (IaC, SDK `railway` + Railway CLI) | En uso |
| Pruebas | pytest (unitarias, arquitectura e integración con PostgreSQL real) | En uso |

## Backend

- **FastAPI** con `uvicorn[standard]`. Arranque desde `backend/` (`uvicorn app.main:app`) o desde la raíz con `--app-dir backend`.
- **Arquitectura hexagonal** (puertos y adaptadores), de cumplimiento obligatorio:
  - `app/core/domain` → entidades y reglas puras. No importa puertos ni casos de uso.
  - `app/core/ports` → contratos (`Protocol`) que exige el Core.
  - `app/core/use_cases` → orquestación; los adaptadores de entrada solo hablan con esta capa.
  - `app/adapters/inbound` → API REST y webhook de Telegram. Reciben casos de uso por inyección (`dependencies.py`) y nunca importan adaptadores de salida.
  - `app/adapters/outbound` → Gemini, tasas FX, PostgreSQL, notificaciones.
  - `app/container.py` → único composition root.
  - `tests/test_architecture.py` falla si se rompe alguna de estas reglas.
- **Imports absolutos** desde `app` (`from app.core.domain.models import ...`). Prohibidos los imports relativos.
- **El Core solo depende de la librería estándar.** Pydantic, FastAPI, asyncpg y los SDK viven en los adaptadores.
- **Persistencia:** asyncpg con SQL explícito (sin ORM). `schema.sql` y `seed.sql` deben ser idempotentes. La migración se controla con `DB_AUTO_MIGRATE` y los datos ficticios con `DB_SEED_DEMO`.
- **Subida de archivos:** `python-multipart`; se aceptan JPG, PNG, WEBP y PDF de hasta 10 MB.
- **Ingesta idempotente:** todo adaptador de entrada entrega a `ProcessInvoiceUseCase` un `external_id` propio del canal (`update_id` en Telegram, header `Idempotency-Key` en web y API, `Message-ID` en email). El puerto genérico `IngestionLog` garantiza que cada `(canal, external_id)` se procese una sola vez. Una repetición devuelve la factura original (`200`; `409` si aún se procesa). Telegram recibe `200 duplicate` si ya se procesó y `503` si aún se procesa, para que reintente. Además, el SHA-256 del archivo refuerza INTEG-01 entre canales: un archivo idéntico a una factura vigente no pasa por el OCR.

## OCR con Gemini

- **SDK oficial `google-genai`** (decisión del 17 de octubre de 2026). Reemplaza a `google-generativeai`, que está deprecado.
- **Modelo:** `gemini-3.8-flash` por defecto (Flash estable vigente según la lista de modelos de Google al 17-oct-2026), configurable con `GEMINI_MODEL`. Las familias 1.5 y 2.0 están retiradas.
- **Salida:** JSON estructurado (`response_json_schema`) con los datos ya normalizados por el modelo: monto numérico, moneda ISO 4217 deducida del documento y fecha ISO. El adaptador solo convierte tipos; las validaciones son de la tubería (INTEG-03, INTEG-04). Moneda ambigua → `XXX`. Ante cualquier falla, el adaptador devuelve una extracción vacía con confianza 0 y la factura escala por INTEG-03 en vez de romper el flujo.
- La llamada usa el cliente asíncrono del SDK (`client.aio.models.generate_content`), sin bloquear el event loop.

## Telegram

- Llamadas directas a la Bot API con `httpx` (`getFile`, `sendMessage`).
- El webhook exige `TELEGRAM_WEBHOOK_SECRET` (header `X-Telegram-Bot-Api-Secret-Token`) y falla cerrado si no está configurado.
- Sin botones de aprobación: Telegram es solo un canal de ingesta.

## Frontend

- React 18 + Vite 5 + Tailwind CSS 3; íconos con lucide-react.
- Tokens de marca Blinka definidos en [DESIGN.md](../docs/diseno/DESIGN.md) (`#04243C`, `#2B9CAE`, `#1D3557`).
- Consume la API REST en `VITE_API_BASE_URL`, con datos de demostración como respaldo si la API no responde.
- Producción: build estático servido por Nginx con la variable `$PORT` de Railway.

## Configuración y repositorio

- **Un solo `.env` en la raíz**, con plantilla en `.env.example`. No se permiten `.env` en subcarpetas.
- **Un solo `.gitignore` en la raíz.**
- Backend: toda variable se lee en `app/config.py` (Settings); ningún otro módulo usa `os.getenv`.
- Documentación en español; READMEs por módulo (`backend/`, `frontend/`) y documentación funcional en `docs/`.
- Licencia MIT.

## Pendientes de limpieza

- Quitar `python-telegram-bot` de `backend/requirements.txt`: no se usa (el cliente va directo con `httpx`).
- Mover `pytest` a dependencias de desarrollo para que no viaje en la imagen de producción.
