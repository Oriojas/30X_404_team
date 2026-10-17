"""
Servidor Principal FastAPI - Blinka PayAgent (Paybot)
Arranca la app, arma el composition root y monta los adaptadores de entrada (REST y Telegram).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.inbound.api.routers import health, invoices, rules
from .adapters.inbound.telegram import webhook as telegram_webhook
from .config import get_settings
from .container import Container

settings = get_settings()

app = FastAPI(
    title="Blinka PayAgent API",
    description="Agente autónomo para procesamiento y auditoría de pagos corporativos en LatAm",
    version="1.0.0"
)
app.state.container = Container(settings)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(invoices.router)
app.include_router(rules.router)
app.include_router(telegram_webhook.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
