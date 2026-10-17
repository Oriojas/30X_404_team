"""
Esquemas Pydantic para validación de datos de entrada y salida en la API.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime


class InvoiceCreateRequest(BaseModel):
    """Payload para procesar una nueva factura manualmente o vía API."""
    invoice_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    original_amount: float = Field(gt=0)
    original_currency: str = "USD"
    due_date: Optional[date] = None
    channel_source: str = "API"


class InvoiceResponse(BaseModel):
    """Respuesta con el dictamen de una factura."""
    id: Optional[int] = None
    invoice_number: str
    vendor_name: str
    original_amount: float
    original_currency: str
    usd_amount: float
    fx_rate_applied: Optional[float] = 1.0
    decision_status: str
    audit_explanation: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyRulesUpdate(BaseModel):
    """Actualización de umbrales desde el Dashboard web."""
    max_autonomous_usd: Optional[float] = None
    sarlaft_check_enabled: Optional[bool] = None
    duplicate_check_days: Optional[int] = None
