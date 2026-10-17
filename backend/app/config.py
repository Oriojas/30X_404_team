"""
Configuración centralizada del Backend.
Lee el `.env` único de la raíz del monorepo; ningún otro módulo debe usar os.getenv.
"""

from functools import lru_cache

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True) or None, extra="ignore")

    port: int = 8000
    environment: str = "development"
    allowed_origins: str = "*"

    database_url: str | None = None
    db_auto_migrate: bool = True   # aplica schema.sql (idempotente)
    db_seed_demo: bool = False     # carga seed.sql con datos ficticios: solo para demo / desarrollo
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None
    telegram_webhook_url: str | None = None   # https://<backend>/api/webhook/telegram (scripts/registrar_webhook.py)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

    company_id: str = "BLINKA_DEFAULT"
    max_autonomous_usd: float = 2000.00
    sarlaft_check_enabled: bool = True
    duplicate_check_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
