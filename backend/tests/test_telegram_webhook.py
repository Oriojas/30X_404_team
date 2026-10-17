"""Pruebas del webhook de Telegram: validación del secret token y extracción de adjuntos."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.telegram import webhook
from app.core.domain.models import DecisionStatus

SECRET = "s3cr3t-token"
PHOTO_UPDATE = {"message": {"chat": {"id": 55}, "photo": [{"file_id": "small"}, {"file_id": "big"}]}}


class FakeFiles:
    def __init__(self):
        self.downloaded = []

    async def download_file(self, file_id):
        self.downloaded.append(file_id)
        return b"bytes"


class FakeProcessInvoice:
    def __init__(self):
        self.calls = []

    async def from_document(self, file_bytes, mime_type, channel_source, chat_id=None):
        self.calls.append((mime_type, channel_source, chat_id))
        return SimpleNamespace(invoice=SimpleNamespace(decision_status=DecisionStatus.SCALED_TO_HUMAN))


def make_client(secret):
    app = FastAPI()
    app.include_router(webhook.router)
    files, use_case = FakeFiles(), FakeProcessInvoice()
    app.state.container = SimpleNamespace(
        settings=SimpleNamespace(telegram_webhook_secret=secret), telegram=files, process_invoice=use_case
    )
    return TestClient(app), files, use_case


def post(client, token=None, body=PHOTO_UPDATE):
    headers = {"X-Telegram-Bot-Api-Secret-Token": token} if token else {}
    return client.post("/api/webhook/telegram", json=body, headers=headers)


def test_webhook_is_disabled_without_configured_secret():
    client, files, _ = make_client(secret=None)
    assert post(client, token="anything").status_code == 503
    assert files.downloaded == []


def test_webhook_rejects_missing_or_wrong_token():
    client, files, use_case = make_client(SECRET)
    assert post(client).status_code == 401
    assert post(client, token="wrong").status_code == 401
    assert files.downloaded == [] and use_case.calls == []


def test_webhook_processes_largest_photo_with_valid_token():
    client, files, use_case = make_client(SECRET)
    response = post(client, token=SECRET)
    assert response.json() == {"status": "processed", "decision": "SCALED_TO_HUMAN"}
    assert files.downloaded == ["big"]
    assert use_case.calls == [("image/jpeg", "TELEGRAM", 55)]


def test_webhook_ignores_messages_without_attachment():
    client, files, _ = make_client(SECRET)
    response = post(client, token=SECRET, body={"message": {"chat": {"id": 1}, "text": "hola"}})
    assert response.json() == {"status": "ignored"} and files.downloaded == []
