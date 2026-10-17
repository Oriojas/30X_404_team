"""Pruebas del webhook de Telegram: validación del secret token y extracción de adjuntos."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.telegram import webhook
from app.core.domain.models import DecisionStatus

SECRET = "s3cr3t-token"
PHOTO_UPDATE = {"update_id": 9001, "message": {"chat": {"id": 55}, "photo": [{"file_id": "small"}, {"file_id": "big"}]}}


class FakeFiles:
    def __init__(self):
        self.downloaded = []

    async def download_file(self, file_id):
        self.downloaded.append(file_id)
        return b"bytes"


class FakeProcessInvoice:
    def __init__(self):
        self.calls = []

    async def from_remote_document(self, load_file, mime_type, channel_source, chat_id=None, external_id=None):
        await load_file()
        self.calls.append((mime_type, channel_source, chat_id, external_id))
        return SimpleNamespace(duplicate=False, in_progress=False,
                               invoice=SimpleNamespace(decision_status=DecisionStatus.SCALED_TO_HUMAN))


def make_client(secret, use_case=None):
    app = FastAPI()
    app.include_router(webhook.router)
    files, use_case = FakeFiles(), use_case or FakeProcessInvoice()
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
    assert use_case.calls == [("image/jpeg", "TELEGRAM", 55, "9001")]


def test_webhook_ignores_messages_without_attachment():
    client, files, _ = make_client(SECRET)
    response = post(client, token=SECRET, body={"message": {"chat": {"id": 1}, "text": "hola"}})
    assert response.json() == {"status": "ignored"} and files.downloaded == []


def real_use_case():
    """ProcessInvoice real con adaptadores falsos y registro de entregas en memoria."""
    from app.core.domain.models import ExtractedInvoice
    from app.core.domain.rules_pipeline import RulesPipeline
    from app.core.use_cases import ProcessInvoiceUseCase

    from .fakes import (
        FakeOCR, FakeRates, FixedTreasury, InMemoryIngestionLog, InMemoryInvoices, InMemoryRules, InMemoryVendors,
        NoSanctions, SpyNotifier,
    )

    invoices, notifier, log = InMemoryInvoices(), SpyNotifier(), InMemoryIngestionLog()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(ExtractedInvoice(invoice_number="F-1", vendor_name="Proveedor Nuevo", original_amount=100)),
        fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=invoices, rules=InMemoryRules(),
        vendors=InMemoryVendors(), sanctions=NoSanctions(), treasury=FixedTreasury(), company_id="TEST",
        notifier=notifier, ingestion=log,
    )
    return use_case, invoices, notifier, log


def test_update_repetido_responde_duplicate_sin_descargar_ni_avisar():
    use_case, invoices, notifier, _ = real_use_case()
    client, files, _ = make_client(SECRET, use_case)

    first = post(client, token=SECRET)
    again = post(client, token=SECRET)

    assert first.json() == {"status": "processed", "decision": "SCALED_TO_HUMAN"}
    assert again.status_code == 200
    assert again.json() == {"status": "duplicate", "decision": "SCALED_TO_HUMAN"}
    assert files.downloaded == ["big"] and len(invoices.items) == 1
    assert len(notifier.received) == 1 and len(notifier.decisions) == 1


def test_update_en_proceso_responde_503_para_que_telegram_reintente():
    import asyncio

    use_case, invoices, notifier, log = real_use_case()
    client, files, _ = make_client(SECRET, use_case)
    asyncio.run(log.claim("TELEGRAM", "9001"))  # la primera entrega sigue procesando

    response = post(client, token=SECRET)
    assert response.status_code == 503
    assert files.downloaded == [] and invoices.items == {} and notifier.received == []

    # La primera entrega falló y liberó la clave: el reintento de Telegram sí se procesa
    asyncio.run(log.release("TELEGRAM", "9001"))
    retry = post(client, token=SECRET)
    assert retry.json() == {"status": "processed", "decision": "SCALED_TO_HUMAN"} and len(invoices.items) == 1


def test_update_distinto_con_el_mismo_archivo_se_frena_por_integ01():
    use_case, invoices, _, _ = real_use_case()
    client, files, _ = make_client(SECRET, use_case)

    post(client, token=SECRET)
    second = post(client, token=SECRET, body={**PHOTO_UPDATE, "update_id": 9002})
    assert second.json() == {"status": "processed", "decision": "REJECTED"}
    assert "INTEG-01" in invoices.items[2].audit_explanation
    assert files.downloaded == ["big", "big"]
