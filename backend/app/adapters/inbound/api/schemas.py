"""
Esquemas Pydantic (DTOs) del adaptador REST.
Traducen JSON <-> entidades del dominio; el Core nunca importa este módulo.
"""

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_serializer

from app.core.domain.models import CompanyRules, ExtractedInvoice, HumanDecision, ProcessedInvoice, TreasuryStatus


class InvoiceCreateRequest(BaseModel):
    """Payload para procesar una nueva factura manualmente o vía API (sin OCR)."""
    invoice_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    bank_account: Optional[str] = None
    original_amount: float = Field(gt=0)
    original_currency: str = "USD"
    due_date: Optional[date] = None
    channel_source: str = "API"

    def to_domain(self) -> ExtractedInvoice:
        return ExtractedInvoice(
            invoice_number=self.invoice_number,
            vendor_name=self.vendor_name,
            vendor_tax_id=self.vendor_tax_id,
            bank_account=self.bank_account,
            original_amount=self.original_amount,
            original_currency=self.original_currency,
            due_date=self.due_date,
        )


class InvoiceResponse(BaseModel):
    """Factura con su dictamen y trazabilidad para el Audit Log."""
    id: Optional[int] = None
    invoice_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    bank_account: Optional[str] = None
    original_amount: float
    original_currency: str
    usd_amount: float
    fx_rate_applied: Optional[float] = 1.0
    due_date: Optional[date] = None
    ocr_confidence_score: Optional[float] = None
    channel_source: str
    decision_status: str
    audit_explanation: str
    evaluations: Dict[str, Any] = {}
    processed_at: datetime
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    human_note: Optional[str] = None

    @field_serializer("processed_at", "decided_at")
    def _as_utc(self, value: Optional[datetime]) -> Optional[str]:
        # La base guarda TIMESTAMP sin zona, siempre en UTC: se marca con "Z" para que el navegador
        # lo convierta a su hora local en vez de tomarlo como hora local.
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def from_domain(cls, invoice: ProcessedInvoice) -> "InvoiceResponse":
        data = asdict(invoice)
        data["decision_status"] = invoice.decision_status.value
        return cls(**data)


class HumanDecisionRequest(BaseModel):
    """Aprobación o rechazo de una factura escalada, desde el dashboard."""
    decision: HumanDecision
    decided_by: str = Field(min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=1000)


class CompanyRulesResponse(BaseModel):
    """Reglas vigentes expuestas al Dashboard."""
    max_autonomous_usd: float
    sarlaft_check_enabled: bool
    duplicate_check_days: int
    min_treasury_buffer_usd: float

    @classmethod
    def from_domain(cls, rules: CompanyRules) -> "CompanyRulesResponse":
        data = asdict(rules)
        data.pop("company_id")
        return cls(**data)


class TreasuryResponse(BaseModel):
    """Liquidez de la cuenta Blinka expuesta al Dashboard."""
    balance_usd: float
    monthly_budget_usd: float
    month_spent_usd: float

    @classmethod
    def from_domain(cls, treasury: TreasuryStatus) -> "TreasuryResponse":
        return cls(**asdict(treasury))


class CompanyRulesUpdate(BaseModel):
    """Actualización de umbrales desde el Dashboard web."""
    max_autonomous_usd: Optional[float] = Field(default=None, ge=0)
    sarlaft_check_enabled: Optional[bool] = None
    duplicate_check_days: Optional[int] = Field(default=None, ge=1, le=365)
    min_treasury_buffer_usd: Optional[float] = Field(default=None, ge=0)
