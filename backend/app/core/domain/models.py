"""
Entidades del Dominio
Modelos puros (dataclasses) que circulan dentro del Core. No dependen de FastAPI, Pydantic ni SQL.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class DecisionStatus(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    SCALED_TO_HUMAN = "SCALED_TO_HUMAN"
    REJECTED = "REJECTED"


@dataclass
class ExtractedInvoice:
    """Datos estructurados que entrega el OCR (o una carga manual vía API)."""
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    original_amount: float
    original_currency: str = "USD"
    vendor_tax_id: Optional[str] = None
    due_date: Optional[date] = None
    ocr_confidence_score: float = 1.0


@dataclass
class CompanyRules:
    """Umbrales y políticas configurables por empresa."""
    company_id: str = "BLINKA_DEFAULT"
    max_autonomous_usd: float = 2000.00
    sarlaft_check_enabled: bool = True
    duplicate_check_days: int = 30
    min_treasury_buffer_usd: float = 10000.00


@dataclass
class Decision:
    """Dictamen de la tubería de reglas."""
    status: DecisionStatus
    explanation: str
    evaluations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedInvoice:
    """Factura evaluada, lista para persistir y mostrar en el Audit Log."""
    invoice_number: str
    vendor_name: str
    original_amount: float
    original_currency: str
    usd_amount: float
    fx_rate_applied: float
    decision_status: DecisionStatus
    audit_explanation: str
    vendor_tax_id: Optional[str] = None
    due_date: Optional[date] = None
    channel_source: str = "API"
    evaluations: Dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
