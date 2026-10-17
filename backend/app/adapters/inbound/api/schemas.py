"""
Esquemas Pydantic (DTOs) del adaptador REST.
Traducen JSON <-> entidades del dominio; el Core nunca importa este módulo.
"""

from dataclasses import asdict
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from ....core.domain.models import CompanyRules, ExtractedInvoice, ProcessedInvoice


class InvoiceCreateRequest(BaseModel):
    """Payload para procesar una nueva factura manualmente o vía API."""
    invoice_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    original_amount: float = Field(gt=0)
    original_currency: str = "USD"
    due_date: Optional[date] = None
    channel_source: str = "API"

    def to_domain(self) -> ExtractedInvoice:
        return ExtractedInvoice(
            invoice_number=self.invoice_number,
            vendor_name=self.vendor_name,
            vendor_tax_id=self.vendor_tax_id,
            original_amount=self.original_amount,
            original_currency=self.original_currency,
            due_date=self.due_date,
        )


class InvoiceResponse(BaseModel):
    """Respuesta con el dictamen de una factura."""
    id: Optional[int] = None
    invoice_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    original_amount: float
    original_currency: str
    usd_amount: float
    fx_rate_applied: Optional[float] = 1.0
    channel_source: str
    decision_status: str
    audit_explanation: str
    processed_at: datetime

    @classmethod
    def from_domain(cls, invoice: ProcessedInvoice) -> "InvoiceResponse":
        data = asdict(invoice)
        data["decision_status"] = invoice.decision_status.value
        return cls(**data)


class CompanyRulesResponse(BaseModel):
    """Reglas vigentes expuestas al Dashboard."""
    max_autonomous_usd: float
    sarlaft_check_enabled: bool
    duplicate_check_days: int
    min_treasury_buffer_usd: float

    @classmethod
    def from_domain(cls, rules: CompanyRules) -> "CompanyRulesResponse":
        return cls(**asdict(rules))


class CompanyRulesUpdate(BaseModel):
    """Actualización de umbrales desde el Dashboard web."""
    max_autonomous_usd: Optional[float] = None
    sarlaft_check_enabled: Optional[bool] = None
    duplicate_check_days: Optional[int] = None
    min_treasury_buffer_usd: Optional[float] = None
