"""Adaptadores falsos en memoria para probar los casos de uso sin infraestructura."""

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.core.domain.models import (
    CompanyRules,
    DecisionStatus,
    ExtractedInvoice,
    IngestionRecord,
    IngestionStatus,
    TreasuryStatus,
)

APPROVED = {DecisionStatus.AUTO_APPROVED, DecisionStatus.HUMAN_APPROVED}


class FakeOCR:
    def __init__(self, extracted: ExtractedInvoice):
        self.extracted = extracted

    async def extract_invoice_data(self, file_bytes, mime_type):
        return self.extracted


class FakeGenAIClient:
    """Imita client.aio.models.generate_content de google-genai y guarda las llamadas."""

    def __init__(self, text=None, error=None, delay=0):
        self.calls = []
        self._text, self._error, self._delay = text, error, delay
        self.aio = SimpleNamespace(models=SimpleNamespace(generate_content=self._generate_content))

    async def _generate_content(self, **kwargs):
        self.calls.append(kwargs)
        await asyncio.sleep(self._delay)
        if self._error:
            raise self._error
        return SimpleNamespace(text=self._text)


class FakeRates:
    async def get_rate_to_usd(self, currency):
        return {"COP": 4200.0, "MXN": 19.5}.get(currency)


class InMemoryInvoices:
    def __init__(self):
        self.items = {}

    async def save(self, invoice):
        invoice = replace(invoice, id=len(self.items) + 1)
        self.items[invoice.id] = invoice
        return invoice

    async def get(self, invoice_id):
        invoice = self.items.get(invoice_id)
        await asyncio.sleep(0)  # simula latencia de la BD: el dato leído puede quedar obsoleto (prueba de concurrencia)
        return invoice

    async def list_recent(self, limit=50):
        return list(self.items.values())[:limit]

    async def update_decision(self, invoice_id, status, explanation, decided_by, decided_at, note, expected_status):
        if self.items[invoice_id].decision_status != expected_status:
            return None
        updated = replace(self.items[invoice_id], decision_status=status, audit_explanation=explanation,
                          decided_by=decided_by, decided_at=decided_at, human_note=note)
        self.items[invoice_id] = updated
        return updated

    async def exists_duplicate(self, vendor_tax_id, vendor_name, invoice_number, usd_amount, within_days):
        return any(i.vendor_name == vendor_name
                   and (i.invoice_number == invoice_number or (usd_amount is not None and i.usd_amount == usd_amount))
                   and i.decision_status not in {DecisionStatus.REJECTED, DecisionStatus.HUMAN_REJECTED}
                   for i in self.items.values())

    async def find_by_file_hash(self, file_sha256, within_days):
        matches = [i for i in self.items.values()
                   if i.file_sha256 == file_sha256
                   and i.processed_at >= datetime.utcnow() - timedelta(days=within_days)
                   and i.decision_status not in {DecisionStatus.REJECTED, DecisionStatus.HUMAN_REJECTED}]
        return matches[-1] if matches else None

    async def vendor_has_paid_history(self, vendor_tax_id, vendor_name):
        return any(i.vendor_name == vendor_name and i.decision_status in APPROVED for i in self.items.values())

    async def sum_approved_usd_since(self, since: datetime):
        return sum(i.usd_amount for i in self.items.values() if i.decision_status in APPROVED)


class InMemoryRules:
    async def get(self, company_id):
        return CompanyRules(company_id="TEST")

    async def save(self, rules):
        return rules


class InMemoryVendors:
    def __init__(self, *vendors):
        self.vendors = vendors

    async def find(self, tax_id, name):
        return next((v for v in self.vendors if v.tax_id == tax_id or v.legal_name == name), None)


class NoSanctions:
    async def find_match(self, name, tax_id, bank_account):
        return None


class FixedTreasury:
    async def get(self, company_id):
        return TreasuryStatus(balance_usd=8500, monthly_budget_usd=25000)


class SpyNotifier:
    def __init__(self):
        self.received, self.decisions = [], []

    async def notify_received(self, invoice_channel, chat_id):
        self.received.append((invoice_channel, chat_id))

    async def notify_decision(self, invoice):
        self.decisions.append(invoice)


class InMemoryIngestionLog:
    """Imita el INSERT ... ON CONFLICT: el lock hace atómico el reclamo entre corrutinas."""

    def __init__(self):
        self.records = {}
        self._lock = asyncio.Lock()

    async def claim(self, channel, external_id):
        async with self._lock:
            existing = self.records.get((channel, external_id))
            if existing:
                return replace(existing)
            self.records[(channel, external_id)] = IngestionRecord(status=IngestionStatus.PROCESSING)
            return None

    async def complete(self, channel, external_id, invoice_id):
        self.records[(channel, external_id)] = IngestionRecord(IngestionStatus.COMPLETED, invoice_id)

    async def release(self, channel, external_id):
        record = self.records.get((channel, external_id))
        if record and record.status == IngestionStatus.PROCESSING:
            del self.records[(channel, external_id)]
