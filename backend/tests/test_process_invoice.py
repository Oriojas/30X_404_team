"""
Pruebas del caso de uso ProcessInvoice con adaptadores falsos.
Demuestran que el Core funciona sin Gemini, PostgreSQL ni Telegram.
"""

import asyncio

from app.core.domain.fx_converter import FXConverter
from app.core.domain.models import CompanyRules, DecisionStatus, ExtractedInvoice
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import ProcessInvoiceUseCase


class FakeOCR:
    async def extract_invoice_data(self, file_bytes, mime_type):
        return ExtractedInvoice(
            invoice_number="FAC-001", vendor_name="Proveedor SAS",
            original_amount=1_500_000, original_currency="COP",
        )


class FakeRates:
    async def get_rate_to_usd(self, currency):
        return 4200.0


class InMemoryInvoices:
    def __init__(self):
        self.saved = []

    async def save(self, invoice):
        invoice.id = len(self.saved) + 1
        self.saved.append(invoice)
        return invoice

    async def list_recent(self, limit=50):
        return self.saved[:limit]

    async def exists_duplicate(self, vendor_tax_id, invoice_number, within_days):
        return False


class InMemoryRules:
    async def get(self, company_id):
        return CompanyRules()

    async def save(self, rules):
        return rules


class SpyNotifier:
    def __init__(self):
        self.sent = []

    async def send_decision(self, chat_id, invoice):
        self.sent.append((chat_id, invoice))
        return True


def test_process_document_converts_persists_and_notifies():
    invoices, notifier = InMemoryInvoices(), SpyNotifier()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(), fx_converter=FXConverter(FakeRates()), pipeline=RulesPipeline(),
        invoices=invoices, rules=InMemoryRules(), notifier=notifier,
    )

    result = asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=42))

    assert result.usd_amount == 357.14
    assert result.fx_rate_applied == 4200.0
    assert result.decision_status == DecisionStatus.AUTO_APPROVED
    assert result.channel_source == "TELEGRAM"
    assert invoices.saved == [result]
    assert notifier.sent == [(42, result)]
