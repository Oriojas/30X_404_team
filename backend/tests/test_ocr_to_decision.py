"""
De la subida a la decisión: POST /api/invoices/upload -> ProcessInvoiceUseCase -> GeminiOCRAdapter (cliente simulado)
-> tubería de 4 capas. Cubre el camino de F1.7 sin PostgreSQL ni la API real de Gemini.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import invoices
from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter
from app.core.domain.models import Vendor
from app.core.domain.rules_pipeline import RulesPipeline, _normalize
from app.core.use_cases import ProcessInvoiceUseCase

from .fakes import (
    FakeGenAIClient, FakeRates, FixedTreasury, InMemoryInvoices, InMemoryRules, InMemoryVendors, NoSanctions,
    SpyNotifier,
)

FIXTURES = Path(__file__).parent / "fixtures"

GLOBAL_TRADE = Vendor("PA-155-7788", "Global Trade Partners Ltd", bank_account="PA-BANCO-PACIFICO-998877",
                      contract_amount_usd=3000)


class OFACList:
    """Lista restrictiva con el proveedor de TC-06; compara con la llave de vendor_key, como PostgreSQL."""

    async def find_match(self, name, tax_id, bank_account):
        for received, listed in ((name, GLOBAL_TRADE.legal_name), (tax_id, GLOBAL_TRADE.tax_id),
                                 (bank_account, GLOBAL_TRADE.bank_account)):
            if _normalize(received) and _normalize(received) == _normalize(listed):
                return f"OFAC: {GLOBAL_TRADE.legal_name}"
        return None


def upload(gemini_json, sanctions, fixture="factura_global_trade.png"):
    use_case = ProcessInvoiceUseCase(
        ocr=GeminiOCRAdapter("test-key", "gemini-test", client=FakeGenAIClient(text=json.dumps(gemini_json))),
        fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=InMemoryInvoices(), rules=InMemoryRules(),
        vendors=InMemoryVendors(GLOBAL_TRADE), sanctions=sanctions, treasury=FixedTreasury(),
        company_id="TEST", notifier=SpyNotifier(),
    )
    app = FastAPI()
    app.include_router(invoices.router)
    app.state.container = SimpleNamespace(process_invoice=use_case)
    with open(FIXTURES / fixture, "rb") as file:
        response = TestClient(app).post("/api/invoices/upload", files={"file": (fixture, file, "image/png")})
    assert response.status_code == 201
    return response.json()


def global_trade_json(**overrides):
    return {
        "invoice_number": "GTP-0091", "vendor_name": "Global Trade Partners Ltd", "vendor_tax_id": "PA-155-7788",
        "bank_account": "PA-BANCO-PACIFICO-998877", "amount": 900.0, "currency": "USD",
        "due_date": "2026-11-20", "confidence": 0.97, **overrides,
    }


def test_factura_de_proveedor_en_lista_ofac_queda_rechazada():
    body = upload(global_trade_json(), OFACList())
    assert body["decision_status"] == "REJECTED"
    assert "COMP-01" in body["audit_explanation"]
    assert body["invoice_number"] == "GTP-0091" and body["usd_amount"] == 900.0


def test_moneda_ambigua_del_ocr_escala_por_integ_04():
    body = upload(global_trade_json(currency=None), NoSanctions())
    assert body["decision_status"] == "SCALED_TO_HUMAN"
    assert "INTEG-04" in body["audit_explanation"]


def test_confianza_nan_del_ocr_escala_por_integ_03():
    body = upload(global_trade_json(confidence=float("nan")), NoSanctions())
    assert body["decision_status"] == "SCALED_TO_HUMAN"
    assert "INTEG-03" in body["audit_explanation"]
