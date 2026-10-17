"""
Prueba de integración contra PostgreSQL real con el seed de demostración (TC-01..TC-06 vía API REST).
Se ejecuta solo si TEST_DATABASE_URL apunta a una base desechable:
    TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/blinka_test pytest
"""

import json
import os
from pathlib import Path

import pytest

from .fakes import FakeGenAIClient

FIXTURES = Path(__file__).parent / "fixtures"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL no configurado")


@pytest.fixture()
def client(monkeypatch):
    import asyncpg
    import asyncio
    from fastapi.testclient import TestClient

    async def reset():
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        await conn.execute("DROP TABLE IF EXISTS invoices, vendors, sanctions_list, treasury_accounts, company_rules")
        await conn.close()

    asyncio.run(reset())
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("DB_AUTO_MIGRATE", "true")
    monkeypatch.setenv("DB_SEED_DEMO", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")  # nunca llamar a la API real desde pytest

    from app.config import get_settings
    from app.container import Container
    from app.main import app

    get_settings.cache_clear()
    app.state.container = Container(get_settings())
    with TestClient(app) as test_client:
        yield test_client


def post_invoice(client, **payload):
    response = client.post("/api/invoices", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_suite_against_seeded_database(client):
    assert client.get("/api/health").json()["database"] == "connected"
    assert len(client.get("/api/invoices").json()) == 5

    tc01 = post_invoice(client, invoice_number="AWS-2026-10", vendor_name="Amazon Web Services LATAM",
                        vendor_tax_id="US-91-1646860", original_amount=450)
    assert tc01["decision_status"] == "AUTO_APPROVED", tc01["audit_explanation"]

    tc02 = post_invoice(client, invoice_number="DS-1042", vendor_name="DevStudio LatAm S.A.S.",
                        vendor_tax_id="900.584.112-4", original_amount=5040000, original_currency="COP")
    assert tc02["decision_status"] == "REJECTED" and "INTEG-01" in tc02["audit_explanation"]

    tc03 = post_invoice(client, invoice_number="DC-001", vendor_name="Diseño Creativo Bogotá S.A.S.",
                        original_amount=800)
    assert tc03["decision_status"] == "SCALED_TO_HUMAN" and "HITL-02" in tc03["audit_explanation"]

    tc04 = post_invoice(client, invoice_number="NA-090", vendor_name="Nube Andina Consultores S.A.S.",
                        vendor_tax_id="901.223.450-1", original_amount=3500)
    assert tc04["decision_status"] == "SCALED_TO_HUMAN" and "HITL-01" in tc04["audit_explanation"]

    tc05 = post_invoice(client, invoice_number="LEM-3400", vendor_name="Logística Express MX S.A. de C.V.",
                        vendor_tax_id="LEM850101AB1", original_amount=195000, original_currency="MXN")
    assert tc05["decision_status"] == "SCALED_TO_HUMAN" and "FIN-01" in tc05["audit_explanation"]

    tc06 = post_invoice(client, invoice_number="GTP-01", vendor_name="Global Trade Partners Ltd",
                        vendor_tax_id="PA-155-7788", bank_account="PA-BANCO-PACIFICO-998877", original_amount=900)
    assert tc06["decision_status"] == "REJECTED" and "COMP-01" in tc06["audit_explanation"]

    gbp = post_invoice(client, invoice_number="AWS-GBP-1", vendor_name="Amazon Web Services LATAM",
                       vendor_tax_id="US-91-1646860", original_amount=1000, original_currency="GBP")
    assert gbp["decision_status"] == "SCALED_TO_HUMAN" and "INTEG-04" in gbp["audit_explanation"]
    assert gbp["usd_amount"] == 0.0 and gbp["fx_rate_applied"] is None

    decision = client.post(f"/api/invoices/{tc04['id']}/decision",
                           json={"decision": "APPROVE", "decided_by": "CFO Blinka", "note": "Contrato vigente"})
    assert decision.status_code == 200 and decision.json()["decision_status"] == "HUMAN_APPROVED"
    assert client.post(f"/api/invoices/{tc04['id']}/decision",
                       json={"decision": "REJECT", "decided_by": "CFO"}).status_code == 409
    assert client.post("/api/invoices/9999/decision", json={"decision": "REJECT", "decided_by": "CFO"}).status_code == 404

    rules = client.post("/api/rules", json={"max_autonomous_usd": 5000}).json()
    assert rules["max_autonomous_usd"] == 5000 and client.get("/api/rules").json()["max_autonomous_usd"] == 5000

    upload = client.post("/api/invoices/upload", files={"file": ("f.png", b"\x89PNG fake", "image/png")})
    assert upload.status_code == 201 and upload.json()["decision_status"] == "SCALED_TO_HUMAN"
    assert upload.json()["channel_source"] == "WEB"
    assert client.post("/api/invoices/upload", files={"file": ("f.txt", b"x", "text/plain")}).status_code == 415


def gemini_reads(invoice_number, vendor_name, tax_id, bank_account, amount, currency, due_date):
    """Respuesta simulada de Gemini con lo que se lee en el fixture (ver tests/fixtures/README.md)."""
    return json.dumps({"invoice_number": invoice_number, "vendor_name": vendor_name, "vendor_tax_id": tax_id,
                       "bank_account": bank_account, "amount": amount, "currency": currency,
                       "due_date": due_date, "confidence": 0.98})


def test_upload_de_fixtures_produce_la_decision_esperada_con_el_seed(client):
    """F1.7: subida real por la API + PostgreSQL con seed; solo el cliente de Gemini es simulado."""
    from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter

    cases = [
        ("factura_devstudio.png", "image/png",
         gemini_reads("DS-2026-1107", "DevStudio LatAm S.A.S.", "900.584.112-4", "CO-BANCOLOMBIA-11122233344",
                      4200000.0, "COP", "2026-11-30"),
         "AUTO_APPROVED", None),
        ("factura_nube_andina.pdf", "application/pdf",
         gemini_reads("NA-4521", "Nube Andina Consultores S.A.S.", "901.223.450-1", "CO-DAVIVIENDA-55566677788",
                      12600000.0, "COP", "2026-12-05"),
         "SCALED_TO_HUMAN", "HITL-01"),
        ("factura_global_trade.png", "image/png",
         gemini_reads("GTP-0091", "Global Trade Partners Ltd", "PA-155-7788", "PA-BANCO-PACIFICO-998877",
                      900.0, "USD", "2026-11-20"),
         "REJECTED", "COMP-01"),
    ]
    process_invoice = client.app.state.container.process_invoice
    for fixture, mime_type, gemini_json, expected_status, expected_code in cases:
        process_invoice.ocr = GeminiOCRAdapter("test-key", "gemini-test", client=FakeGenAIClient(text=gemini_json))
        with open(FIXTURES / fixture, "rb") as file:
            response = client.post("/api/invoices/upload", files={"file": (fixture, file, mime_type)})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["decision_status"] == expected_status, (fixture, body["audit_explanation"])
        if expected_code:
            assert expected_code in body["audit_explanation"]
        assert body["channel_source"] == "WEB"

    stored = {inv["invoice_number"]: inv["decision_status"] for inv in client.get("/api/invoices").json()}
    assert stored["DS-2026-1107"] == "AUTO_APPROVED" and stored["GTP-0091"] == "REJECTED"
