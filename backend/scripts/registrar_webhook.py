"""
Registra el webhook de Telegram con el secret token (Fase 4, F4.3).
Lee TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL y TELEGRAM_WEBHOOK_SECRET del `.env` de la raíz
(o del entorno, p. ej. con `railway run`). Nunca imprime el token.

Uso (desde backend/):
    python -m scripts.registrar_webhook            # setWebhook y luego muestra getWebhookInfo
    python -m scripts.registrar_webhook --info     # solo consulta el estado
    python -m scripts.registrar_webhook --borrar   # deleteWebhook (para volver a local)
"""

import argparse
import sys

import httpx

from app.config import Settings, get_settings

TELEGRAM_API = "https://api.telegram.org"
WEBHOOK_PATH = "/api/webhook/telegram"


class ConfigError(Exception):
    pass


def _require(settings: Settings, *names: str) -> None:
    missing = [name.upper() for name in names if not getattr(settings, name)]
    if missing:
        raise ConfigError(f"Faltan variables: {', '.join(missing)}.")


def _call(client: httpx.Client, token: str, method: str, payload: dict | None = None) -> dict:
    response = client.post(f"{TELEGRAM_API}/bot{token}/{method}", json=payload or {})
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f"{method} falló: respuesta no JSON (HTTP {response.status_code})") from None
    if not isinstance(data, dict) or not data.get("ok"):
        raise RuntimeError(f"{method} falló: {data.get('description', response.status_code)}")
    return data["result"]


def registrar(client: httpx.Client, settings: Settings) -> dict:
    _require(settings, "telegram_bot_token", "telegram_webhook_url", "telegram_webhook_secret")
    url = settings.telegram_webhook_url
    if not url.startswith("https://") or not url.endswith(WEBHOOK_PATH):
        raise ConfigError(f"TELEGRAM_WEBHOOK_URL debe ser https://<backend>{WEBHOOK_PATH}")
    _call(client, settings.telegram_bot_token, "setWebhook", {
        "url": url,
        "secret_token": settings.telegram_webhook_secret,
        "allowed_updates": ["message"],
        # False: re-registrar (p. ej. al rotar el secreto) no descarta facturas que Telegram tenga en cola
        "drop_pending_updates": False,
    })
    return info(client, settings)


def info(client: httpx.Client, settings: Settings) -> dict:
    _require(settings, "telegram_bot_token")
    return _call(client, settings.telegram_bot_token, "getWebhookInfo")


def borrar(client: httpx.Client, settings: Settings) -> None:
    _require(settings, "telegram_bot_token")
    _call(client, settings.telegram_bot_token, "deleteWebhook", {"drop_pending_updates": True})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--info", action="store_true", help="solo consultar getWebhookInfo")
    group.add_argument("--borrar", action="store_true", help="eliminar el webhook")
    args = parser.parse_args()

    settings = get_settings()
    try:
        with httpx.Client(timeout=15) as client:
            if args.borrar:
                borrar(client, settings)
                print("Webhook eliminado.")
                return
            result = info(client, settings) if args.info else registrar(client, settings)
    except (ConfigError, RuntimeError, httpx.HTTPError) as error:
        sys.exit(str(error))

    print(f"url:                  {result.get('url') or '(sin webhook)'}")
    print(f"pending_update_count: {result.get('pending_update_count', 0)}")
    print(f"last_error_message:   {result.get('last_error_message') or '-'}")


if __name__ == "__main__":
    main()
