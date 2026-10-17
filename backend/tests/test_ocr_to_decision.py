"""
Del OCR a la decisión: GeminiOCRAdapter (con cliente simulado) conectado a ProcessInvoiceUseCase.
Demuestra que lo que entrega Gemini llega a la tubería y produce la decisión esperada.
"""

import asyncio
import json
from pathlib import Path

from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter
from app.core.domain.models import DecisionStatus, Vendor
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import ProcessInvoiceUseCase

from .fakes import FakeRates, FixedTreasury, InMemoryInvoices, InMemoryRules, InMemoryVendors, NoSanctions, SpyNotifier
from .test_gemini_ocr import FakeGenAIClient

FIXTURES = Path(__file__).parent / "fixtures"

GLOBAL_TRADE = Vendor("PA-155-7788", "Global Trade Partners Ltd", bank_account="PA-BANCO-PACIFICO-998877",
                      contract_amount_usd=3000)


class OFACList:
    """Lista restrictiva con el proveedor de TC-06."""

    async def find_match(self, name, tax_id, bank_account):
        if bank_account == GLOBAL_TRADE.bank_account or tax_id == GLOBAL_TRADE.tax_id:
            return f"OFAC: {GLOBAL_TRADE.legal_name}"
        return None


def process(gemini_json, fixture, sanctions):
    use_case = ProcessInvoiceUseCase(
        ocr=GeminiOCRAdapter("test-key", "gemini-test", client=FakeGenAIClient(text=json.dumps(gemini_json))),
        fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=InMemoryInvoices(), rules=InMemoryRules(),
        vendors=InMemoryVendors(GLOBAL_TRADE), sanctions=sanctions, treasury=FixedTreasury(),
        company_id="TEST", notifier=SpyNotifier(),
    )
    return asyncio.run(use_case.from_document((FIXTURES / fixture).read_bytes(), "image/png", "WEB"))


def global_trade_json(**overrides):
    return {
        "invoice_number": "GTP-0091", "vendor_name": "Global Trade Partners Ltd", "vendor_tax_id": "PA-155-7788",
        "bank_account": "PA-BANCO-PACIFICO-998877", "amount": 900.0, "currency": "USD",
        "due_date": "2026-11-20", "confidence": 0.97, **overrides,
    }


def test_factura_de_proveedor_en_lista_ofac_queda_rechazada():
    result = process(global_trade_json(), "factura_global_trade.png", OFACList())
    assert result.decision_status == DecisionStatus.REJECTED
    assert "COMP-01" in result.audit_explanation
    assert result.invoice_number == "GTP-0091" and result.usd_amount == 900.0


def test_moneda_ambigua_del_ocr_escala_por_integ_04():
    result = process(global_trade_json(currency=None), "factura_global_trade.png", NoSanctions())
    assert result.decision_status == DecisionStatus.SCALED_TO_HUMAN
    assert "INTEG-04" in result.audit_explanation
