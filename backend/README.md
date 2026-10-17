# Blinka PayAgent — Backend API

Servicio backend desarrollado en **Python 3.12** con **FastAPI** bajo **Arquitectura Hexagonal (Puertos y Adaptadores)**. Se encarga de la ingesta de documentos contables, extracción con visión multimodal mediante **Gemini 1.5 Flash**, conversión de divisas con **$0.00 FX Markup**, evaluación en una tubería de 4 capas de negocio y persistencia en **PostgreSQL**.

---

## 🏛️ Arquitectura Hexagonal

```text
backend/app/
├── adapters/
│   ├── channels/
│   │   └── telegram_bot.py      # Adaptador de entrada: Webhook de Telegram (fotos y PDFs)
│   └── db/
│       ├── postgres_adapter.py  # Adaptador de salida: Conexión y operaciones PostgreSQL
│       └── schema.sql           # DDL inicial de tablas (company_rules, invoices)
├── core/                        # Lógica de Negocio Pura (Independiente del framework)
│   ├── ocr_engine.py            # Extracción estructurada JSON con Gemini 1.5 Flash
│   ├── fx_converter.py          # Conversión multidivisa (COP/MXN/EUR -> USD) a tasa interbancaria
│   ├── rules_pipeline.py        # Tubería determinista de 4 capas (Cumplimiento, Integridad, Solvencia, HITL)
│   └── audit_logger.py          # Generador de explicabilidad en lenguaje natural
├── models/
│   └── schemas.py               # Modelos de datos y contratos Pydantic
└── main.py                      # Punto de entrada FastAPI, middlewares y rutas REST
```

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

Consulta la plantilla completa en [.env.example](file:///home/oscar/Github/30X_404_team/.env.example).

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

---

## 🐳 Despliegue con Docker (Railway)

El archivo [Dockerfile](file:///home/oscar/Github/30X_404_team/backend/Dockerfile) empaqueta la aplicación con Python 3.12-slim:

```bash
docker build -t blinka-backend -f backend/Dockerfile .
docker run -p 8000:8000 --env-file .env blinka-backend
```

En Railway, la variable `$PORT` es asignada en runtime y el contenedor arranca automáticamente con `uvicorn`.

---

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Verificación de estado del servicio y PostgreSQL |
| `POST` | `/api/webhook/telegram` | Webhook de ingesta para fotos y documentos de Telegram |
| `GET` | `/api/invoices` | Listado histórico de facturas y decisiones del Audit Log |
| `POST` | `/api/invoices` | Creación y evaluación manual de facturas |
| `GET` | `/api/rules` | Consulta de reglas de negocio actuales |
| `POST` | `/api/rules` | Actualización de umbrales autónomos y políticas |

---

## 🔗 Referencias
* [README Principal del Proyecto](file:///home/oscar/Github/30X_404_team/README.md)
* [Frontend (React + Tailwind)](file:///home/oscar/Github/30X_404_team/frontend/README.md)
* [Arquitectura de Solución v4](file:///home/oscar/Github/30X_404_team/docs/arquitectura/arquitectura_solucion_v4.md)
