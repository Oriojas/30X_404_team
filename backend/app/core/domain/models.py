"""
Entidades del Dominio
Modelos puros (dataclasses) que circulan dentro del Core. No dependen de FastAPI, Pydantic ni SQL.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionStatus(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    SCALED_TO_HUMAN = "SCALED_TO_HUMAN"
    REJECTED = "REJECTED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"


class HumanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class IngestionStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


@dataclass
class ExtractedInvoice:
    """Datos estructurados que entrega el OCR (o una carga manual vía API)."""
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    original_amount: float
    original_currency: str = "USD"
    vendor_tax_id: Optional[str] = None
    bank_account: Optional[str] = None
    due_date: Optional[date] = None
    ocr_confidence_score: float = 1.0


@dataclass
class CompanyRules:
    """Umbrales y políticas configurables por empresa."""
    company_id: str
    max_autonomous_usd: float = 2000.00
    sarlaft_check_enabled: bool = True
    duplicate_check_days: int = 30
    min_treasury_buffer_usd: float = 1000.00


@dataclass
class Vendor:
    """Proveedor verificado en el registro de la empresa."""
    tax_id: str
    legal_name: str
    bank_account: Optional[str] = None
    is_pep: bool = False
    contract_amount_usd: Optional[float] = None


@dataclass
class TreasuryStatus:
    """Liquidez de la cuenta Blinka en USD al momento de evaluar."""
    balance_usd: float
    monthly_budget_usd: float
    month_spent_usd: float = 0.0


@dataclass
class RuleAlert:
    """Regla disparada por la tubería (código de la matriz v3)."""
    code: str
    severity: DecisionStatus  # REJECTED o SCALED_TO_HUMAN
    message: str


@dataclass
class Decision:
    """Dictamen de la tubería de reglas."""
    status: DecisionStatus
    explanation: str
    evaluations: Dict[str, Any] = field(default_factory=dict)
    alerts: List[RuleAlert] = field(default_factory=list)


@dataclass
class ProcessedInvoice:
    """Factura evaluada, lista para persistir y mostrar en el Audit Log."""
    invoice_number: str
    vendor_name: str
    original_amount: float
    original_currency: str
    usd_amount: float
    fx_rate_applied: Optional[float]
    decision_status: DecisionStatus
    audit_explanation: str
    vendor_tax_id: Optional[str] = None
    bank_account: Optional[str] = None
    due_date: Optional[date] = None
    ocr_confidence_score: Optional[float] = None
    channel_source: str = "API"
    source_chat_id: Optional[int] = None
    evaluations: Dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.utcnow)
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    human_note: Optional[str] = None
    file_sha256: Optional[str] = None
    id: Optional[int] = None


@dataclass
class IngestionRecord:
    """Entrega ya reclamada por un canal: (canal, id externo) se procesa una sola vez."""
    status: IngestionStatus
    invoice_id: Optional[int] = None


@dataclass
class IngestionResult:
    """Resultado de una entrega. Una repetición trae la factura original o, si sigue en proceso, ninguna."""
    invoice: Optional[ProcessedInvoice]
    duplicate: bool = False

    @property
    def in_progress(self) -> bool:
        return self.duplicate and self.invoice is None
