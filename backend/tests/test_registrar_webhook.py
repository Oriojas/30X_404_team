"""Pruebas del script que registra el webhook de Telegram (sin llamar a la API real)."""

import json

import httpx
import pytest

from app.config import Settings
from scripts.registrar_webhook import ConfigError, registrar

URL = "https://backend.example.app/api/webhook/telegram"


def settings(**overrides):
    values = {"telegram_bot_token": "123:abc", "telegram_webhook_url": URL, "telegram_webhook_secret": "s3cr3t"}
    return Settings(_env_file=None, **{**values, **overrides})


def fake_client(calls):
    def handler(request):
        calls.append((request.url.path, json.loads(request.content or b"{}")))
        if request.url.path.endswith("/getWebhookInfo"):
            return httpx.Response(200, json={"ok": True, "result": {"url": URL, "pending_update_count": 0}})
        return httpx.Response(200, json={"ok": True, "result": True})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_registrar_llama_set_webhook_con_el_secreto():
    calls = []
    result = registrar(fake_client(calls), settings())

    path, payload = calls[0]
    assert path == "/bot123:abc/setWebhook"
    assert payload == {"url": URL, "secret_token": "s3cr3t", "allowed_updates": ["message"], "drop_pending_updates": False}
    assert calls[1][0] == "/bot123:abc/getWebhookInfo"
    assert result["url"] == URL


def test_registrar_falla_si_falta_el_secreto():
    calls = []
    with pytest.raises(ConfigError, match="TELEGRAM_WEBHOOK_SECRET"):
        registrar(fake_client(calls), settings(telegram_webhook_secret=None))
    assert calls == []


def test_registrar_exige_https_y_la_ruta_del_webhook():
    with pytest.raises(ConfigError):
        registrar(fake_client([]), settings(telegram_webhook_url="http://backend.example.app/otra"))


def test_registrar_reporta_el_error_de_telegram():
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(401, json={"ok": False, "description": "Unauthorized"})))
    with pytest.raises(RuntimeError, match="Unauthorized"):
        registrar(client, settings())


def test_registrar_reporta_una_respuesta_no_json():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(502, text="<html>Bad Gateway</html>")))
    with pytest.raises(RuntimeError, match="no JSON"):
        registrar(client, settings())
