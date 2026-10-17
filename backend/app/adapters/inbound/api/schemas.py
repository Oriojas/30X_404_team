"""
Esquemas Pydantic (DTOs) del adaptador REST.
Traducen JSON <-> entidades del dominio; el Core nunca importa este módulo.
"""

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from app.core.domain.models import (
    CompanyRules,
    ExtractedInvoice,
    HumanDecision,
    ProcessedInvoice,
    TreasuryStatus,
    Vendor,
)
from app.core.domain.rules_pipeline import _normalize


def _utc_iso(value: Optional[datetime]) -> Optional[str]:
    # La base guarda TIMESTAMP sin zona, siempre en UTC: se marca con "Z" para que el navegador
    # lo convierta a su hora local en vez de tomarlo como hora local.
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
        return _utc_iso(value)

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
    max_payment_usd: float

    @classmethod
    def from_domain(cls, rules: CompanyRules) -> "CompanyRulesResponse":
        data = asdict(rules)
        data.pop("company_id")
        return cls(**data)


class TreasuryResponse(BaseModel):
    """Liquidez de la cuenta Blinka expuesta al Dashboard: saldo de la foto, comprometido y disponible."""
    balance_usd: float
    committed_usd: float
    available_usd: float
    snapshot_at: Optional[datetime] = None
    monthly_budget_usd: float
    month_spent_usd: float

    @field_serializer("snapshot_at")
    def _as_utc(self, value: Optional[datetime]) -> Optional[str]:
        return _utc_iso(value)

    @classmethod
    def from_domain(cls, treasury: TreasuryStatus) -> "TreasuryResponse":
        return cls(**asdict(treasury), available_usd=treasury.available_usd)


class TreasuryBalanceUpdate(BaseModel):
    """Saldo vigente (toma una foto nueva) y/o presupuesto del periodo; al menos uno de los dos."""
    balance_usd: Optional[float] = Field(default=None, gt=0)
    monthly_budget_usd: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _al_menos_un_campo(self) -> "TreasuryBalanceUpdate":
        if self.balance_usd is None and self.monthly_budget_usd is None:
            raise ValueError("Envía balance_usd, monthly_budget_usd o ambos.")
        return self


class CompanyRulesUpdate(BaseModel):
    """Actualización de umbrales desde el Dashboard web."""
    max_autonomous_usd: Optional[float] = Field(default=None, ge=0)
    sarlaft_check_enabled: Optional[bool] = None
    duplicate_check_days: Optional[int] = Field(default=None, ge=1, le=365)
    min_treasury_buffer_usd: Optional[float] = Field(default=None, ge=0)
    max_payment_usd: Optional[float] = Field(default=None, ge=0)


class VendorResponse(BaseModel):
    """Beneficiario de la lista permitida, con su último cambio."""
    id: int
    tax_id: str
    legal_name: str
    bank_account: Optional[str] = None
    is_pep: bool
    contract_amount_usd: Optional[float] = None
    active: bool
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    @field_serializer("updated_at")
    def _as_utc(self, value: Optional[datetime]) -> Optional[str]:
        return _utc_iso(value)

    @classmethod
    def from_domain(cls, vendor: Vendor) -> "VendorResponse":
        return cls(**asdict(vendor))


# Límites iguales a las columnas de vendors: un texto más largo sería un 500 de asyncpg.
# extra="forbid": tax_id o is_pep en el cuerpo responden 422 en vez de ignorarse.
_VENDOR_CONFIG = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _con_letras_o_digitos(value: Optional[str]) -> Optional[str]:
    # La llave de comparación (vendor_key / _normalize) de "---" o "..." es vacía: no identificaría a nadie
    if value is not None and not _normalize(value):
        raise ValueError("Debe tener al menos una letra o un dígito.")
    return value


class VendorCreate(BaseModel):
    """Alta en la lista permitida desde el Dashboard. is_pep queda en False: la condición PEP la define cumplimiento."""
    model_config = _VENDOR_CONFIG
    tax_id: str = Field(min_length=1, max_length=50)
    legal_name: str = Field(min_length=1, max_length=150)
    bank_account: str = Field(min_length=1, max_length=80)
    contract_amount_usd: Optional[float] = Field(default=None, gt=0)
    updated_by: str = Field(min_length=1, max_length=100)

    _llaves = field_validator("tax_id", "legal_name")(_con_letras_o_digitos)


class VendorUpdate(BaseModel):
    """Edición o baja lógica (active = false). contract_amount_usd = null quita la tarifa acordada."""
    model_config = _VENDOR_CONFIG
    legal_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    bank_account: Optional[str] = Field(default=None, min_length=1, max_length=80)
    contract_amount_usd: Optional[float] = Field(default=None, gt=0)
    active: Optional[bool] = None
    updated_by: str = Field(min_length=1, max_length=100)

    _llaves = field_validator("legal_name")(_con_letras_o_digitos)

    @model_validator(mode="after")
    def _sin_nulos_obligatorios(self) -> "VendorUpdate":
        for name in ("legal_name", "bank_account", "active"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} no puede ser null.")
        return self

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True, exclude={"updated_by"})
