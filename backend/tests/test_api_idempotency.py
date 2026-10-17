"""Header Idempotency-Key en POST /api/invoices y /api/invoices/upload (F2.5): 201, 200 y 409."""

import asyncio
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import invoices
from app.core.domain.models import ExtractedInvoice
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import ProcessInvoiceUseCase

from .fakes import (
    FakeOCR, FakeRates, FixedTreasury, InMemoryIngestionLog, InMemoryInvoices, InMemoryRules, InMemoryVendors,
    NoSanctions, SpyNotifier,
)

MANUAL = {"invoice_number": "M-1", "vendor_name": "Proveedor Nuevo", "original_amount": 100}


def make_client():
    store, notifier, log = InMemoryInvoices(), SpyNotifier(), InMemoryIngestionLog()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(ExtractedInvoice(invoice_number="F-1", vendor_name="Proveedor Nuevo", original_amount=100)),
        fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=store, rules=InMemoryRules(),
        vendors=InMemoryVendors(), sanctions=NoSanctions(), treasury=FixedTreasury(), company_id="TEST",
        notifier=notifier, ingestion=log,
    )
    app = FastAPI()
    app.include_router(invoices.router)
    app.state.container = SimpleNamespace(process_invoice=use_case)
    return TestClient(app), store, log


def upload(client, key=None, content=b"\x89PNG factura"):
    headers = {"Idempotency-Key": key} if key is not None else {}
    return client.post("/api/invoices/upload", files={"file": ("f.png", content, "image/png")}, headers=headers)


def create(client, key=None, payload=MANUAL):
    headers = {"Idempotency-Key": key} if key is not None else {}
    return client.post("/api/invoices", json=payload, headers=headers)


def test_subida_repetida_con_la_misma_clave_devuelve_la_misma_factura():
    client, store, _ = make_client()
    first, again = upload(client, "k-1"), upload(client, "k-1")
    assert first.status_code == 201 and again.status_code == 200
    assert again.json() == first.json() and len(store.items) == 1


def test_carga_manual_repetida_con_la_misma_clave_devuelve_la_misma_factura():
    client, store, _ = make_client()
    first, again = create(client, "k-1"), create(client, "k-1")
    assert first.status_code == 201 and again.status_code == 200
    assert again.json()["id"] == first.json()["id"] and len(store.items) == 1


def test_sin_header_cada_solicitud_crea_una_factura():
    client, store, _ = make_client()
    assert create(client).status_code == 201 and create(client).status_code == 201
    assert len(store.items) == 2


def test_clave_en_proceso_responde_409():
    client, store, log = make_client()
    asyncio.run(log.claim("WEB", "k-1"))
    response = upload(client, "k-1")
    assert response.status_code == 409 and "aún se está procesando" in response.json()["detail"]
    assert store.items == {}


def test_la_misma_clave_en_subida_y_carga_manual_no_colisiona():
    client, store, _ = make_client()
    # Aunque el cliente declare channel_source WEB, la carga manual usa su propio espacio de claves
    assert upload(client, "k-1").status_code == 201
    assert create(client, "k-1", {**MANUAL, "channel_source": "WEB"}).status_code == 201
    assert len(store.items) == 2


def test_clave_vacia_o_demasiado_larga_es_invalida():
    client, store, _ = make_client()
    assert upload(client, "").status_code == 422
    assert create(client, "x" * 201).status_code == 422
    assert store.items == {}
