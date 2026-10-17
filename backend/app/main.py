"""
Servidor Principal FastAPI - Blinka PayAgent (Paybot)
Arranca la app, arma el composition root y monta los adaptadores de entrada (REST y Telegram).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.inbound.api.routers import health, invoices, rules, treasury, vendors
from app.adapters.inbound.telegram import webhook as telegram_webhook
from app.adapters.outbound.db.postgres_repository import DatabaseUnavailableError
from app.config import get_settings
from app.container import Container
from app.core.domain.errors import ConflictError, InvalidRulesError, NotFoundError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app.state.container.startup()
    yield
    await app.state.container.shutdown()


app = FastAPI(
    title="Blinka PayAgent API",
    description="Agente autónomo para procesamiento y auditoría de pagos corporativos en LatAm",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.container = Container(settings)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Un handler por tipo de error de dominio: cada error nuevo solo elige su base en errors.py
@app.exception_handler(NotFoundError)
async def not_found(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict(_: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidRulesError)
async def invalid_rules(_: Request, exc: InvalidRulesError):
    # Misma forma que los 422 de FastAPI: el dashboard lo muestra junto al campo (ApiError.fieldErrors)
    return JSONResponse(status_code=422, content={"detail": [{"loc": ["body", exc.field], "msg": str(exc)}]})


@app.exception_handler(DatabaseUnavailableError)
async def database_unavailable(_: Request, exc: DatabaseUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(invoices.router)
app.include_router(rules.router)
app.include_router(treasury.router)
app.include_router(vendors.router)
app.include_router(telegram_webhook.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
