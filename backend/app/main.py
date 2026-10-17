"""
Servidor Principal FastAPI - Blinka PayAgent (Paybot)
Expone la API REST para el Dashboard y recibe Webhooks de Telegram.
"""

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

app = FastAPI(
    title="Blinka PayAgent API",
    description="Agente autónomo para procesamiento y auditoría de pagos corporativos en LatAm",
    version="1.0.0"
)

# Configuración de CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Blinka PayAgent API",
        "status": "online",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/api/health")
async def health_check():
    """Endpoint de estado para Railway y monitoreo."""
    return {"status": "ok"}


@app.post("/api/webhook/telegram")
async def telegram_webhook(request: Request):
    """Webhook para ingesta de fotos y mensajes desde Telegram."""
    payload = await request.json()
    # TODO: Conectar con TelegramChannelAdapter
    return {"status": "processed", "payload_received": bool(payload)}


@app.get("/api/invoices")
async def list_invoices(limit: int = 50):
    """Lista las facturas procesadas para el Dashboard de React."""
    # TODO: Conectar con PostgresDatabaseAdapter
    return {"invoices": []}


@app.get("/api/rules")
async def get_rules():
    """Consulta las reglas y umbrales vigentes para la empresa."""
    # TODO: Conectar con PostgresDatabaseAdapter
    return {
        "max_autonomous_usd": float(os.getenv("MAX_AUTONOMOUS_USD", "2000.00")),
        "sarlaft_check_enabled": os.getenv("SARLAFT_CHECK_ENABLED", "true").lower() == "true",
        "duplicate_check_days": int(os.getenv("DUPLICATE_CHECK_DAYS", "30")),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
