"""Adaptadores falsos en memoria para probar los casos de uso sin infraestructura."""

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.core.domain.errors import TreasuryNotInitializedError
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


class InMemoryRules:
    def __init__(self, **overrides):
        self.overrides = overrides

    async def get(self, company_id):
        return CompanyRules(company_id="TEST", **self.overrides)

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
    """Saldo de $8,500 y presupuesto de $25,000; set_balance toma una foto nueva y libera lo comprometido.
    Con initialized=False imita una base sin fila de tesorería: set_monthly_budget no la crea."""

    def __init__(self, month_spent_usd=0.0, committed_usd=0.0, snapshot_at=None, monthly_budget_usd=25000.0,
                 initialized=True):
        self.balance_usd = 8500.0
        self.monthly_budget_usd = monthly_budget_usd
        self.month_spent_usd = month_spent_usd
        self.committed_usd = committed_usd
        self.snapshot_at = snapshot_at
        self.initialized = initialized

    async def get(self, company_id):
        return TreasuryStatus(balance_usd=self.balance_usd, monthly_budget_usd=self.monthly_budget_usd,
                              month_spent_usd=self.month_spent_usd, committed_usd=self.committed_usd,
                              snapshot_at=self.snapshot_at)

    async def set_balance(self, company_id, balance_usd, as_of, monthly_budget_usd=None):
        self.balance_usd, self.committed_usd, self.snapshot_at = balance_usd, 0.0, as_of
        self.monthly_budget_usd = monthly_budget_usd or self.monthly_budget_usd
        self.initialized = True
        return await self.get(company_id)

    async def set_monthly_budget(self, company_id, monthly_budget_usd):
        if not self.initialized:
            raise TreasuryNotInitializedError(company_id)
        self.monthly_budget_usd = monthly_budget_usd
        return await self.get(company_id)


def approved_at(invoice):
    """Fecha de aprobación como el CASE de PostgresTreasuryRepository.get (D4)."""
    if invoice.decision_status == DecisionStatus.AUTO_APPROVED:
        return invoice.processed_at
    return invoice.decided_at or invoice.processed_at


class LedgerTreasury:
    """Saldo con foto: compromete lo aprobado en InMemoryInvoices después de snapshot_at.
    Lee y luego cede el control, como una consulta real: sin candado, dos evaluaciones ven el mismo disponible."""

    def __init__(self, invoices, balance_usd=8500.0, snapshot_at=None, monthly_budget_usd=25000.0):
        self.invoices, self.balance_usd = invoices, balance_usd
        self.monthly_budget_usd = monthly_budget_usd
        self.snapshot_at = snapshot_at or datetime.utcnow()

    async def get(self, company_id):
        committed = sum(i.usd_amount for i in self.invoices.items.values()
                        if i.decision_status in APPROVED and approved_at(i) > self.snapshot_at)
        await asyncio.sleep(0)  # el resultado llega después: puede quedar obsoleto si nadie serializa
        return TreasuryStatus(balance_usd=self.balance_usd, monthly_budget_usd=self.monthly_budget_usd,
                              committed_usd=committed, snapshot_at=self.snapshot_at)

    async def set_balance(self, company_id, balance_usd, as_of, monthly_budget_usd=None):
        self.balance_usd, self.snapshot_at = balance_usd, as_of
        self.monthly_budget_usd = monthly_budget_usd or self.monthly_budget_usd
        return await self.get(company_id)

    async def set_monthly_budget(self, company_id, monthly_budget_usd):
        self.monthly_budget_usd = monthly_budget_usd
        return await self.get(company_id)


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
