"""
Puertos de Salida
Interfaces que el Core necesita del mundo exterior. Cada adaptador en `adapters/outbound/` implementa una.
"""

from datetime import datetime
from typing import List, Optional, Protocol

from app.core.domain.models import (
    CompanyRules,
    DecisionStatus,
    ExtractedInvoice,
    IngestionRecord,
    ProcessedInvoice,
    TreasuryStatus,
    Vendor,
)


class OCRPort(Protocol):
    """Extracción estructurada de facturas desde imágenes o PDFs."""

    async def extract_invoice_data(self, file_bytes: bytes, mime_type: str) -> ExtractedInvoice: ...


class FXRateProvider(Protocol):
    """Fuente de tasas de cambio (unidades de moneda local por 1 USD)."""

    async def get_rate_to_usd(self, currency: str) -> Optional[float]:
        """Retorna None si la moneda no está soportada (nunca una tasa por defecto)."""
        ...


class InvoiceRepository(Protocol):
    """Persistencia de facturas procesadas y Audit Log."""

    async def save(self, invoice: ProcessedInvoice) -> ProcessedInvoice: ...

    async def get(self, invoice_id: int) -> Optional[ProcessedInvoice]: ...

    async def list_recent(self, limit: int = 50) -> List[ProcessedInvoice]: ...

    async def update_decision(
        self, invoice_id: int, status: DecisionStatus, explanation: str,
        decided_by: str, decided_at: datetime, note: Optional[str], expected_status: DecisionStatus,
    ) -> Optional[ProcessedInvoice]:
        """Actualiza solo si la factura sigue en expected_status (operación atómica); si no, retorna None."""
        ...

    async def exists_duplicate(
        self, vendor_tax_id: Optional[str], vendor_name: Optional[str],
        invoice_number: Optional[str], usd_amount: Optional[float], within_days: int,
    ) -> bool:
        """INTEG-01: mismo número + proveedor, o mismo monto + proveedor, en la ventana (excluye rechazadas).
        Con usd_amount None solo compara por número."""
        ...

    async def find_by_file_hash(self, file_sha256: str, within_days: int) -> Optional[ProcessedInvoice]:
        """INTEG-01 por archivo: la factura más reciente con el mismo SHA-256 en la ventana (excluye rechazadas)."""
        ...

    async def vendor_has_paid_history(self, vendor_tax_id: Optional[str], vendor_name: Optional[str]) -> bool:
        """HITL-02: el proveedor tiene al menos un pago aprobado previo."""
        ...


class RulesRepository(Protocol):
    """Lectura y actualización de reglas corporativas."""

    async def get(self, company_id: str) -> CompanyRules: ...

    async def save(self, rules: CompanyRules) -> CompanyRules: ...


class VendorRepository(Protocol):
    """Registro de proveedores verificados."""

    async def find(self, tax_id: Optional[str], name: Optional[str]) -> Optional[Vendor]: ...


class SanctionsRepository(Protocol):
    """Listas restrictivas OFAC / ONU / GAFI."""

    async def find_match(
        self, name: Optional[str], tax_id: Optional[str], bank_account: Optional[str]
    ) -> Optional[str]:
        """Retorna una descripción de la coincidencia (ej. 'OFAC: Global Trade Partners Ltd') o None."""
        ...


class TreasuryRepository(Protocol):
    """Saldo y presupuesto de la cuenta Blinka, con lo comprometido desde la foto del saldo
    y el acumulado aprobado del mes en curso (FIN-02)."""

    async def get(self, company_id: str) -> TreasuryStatus: ...

    async def set_balance(
        self, company_id: str, balance_usd: float, as_of: datetime, monthly_budget_usd: Optional[float] = None
    ) -> TreasuryStatus:
        """Toma una foto nueva del saldo a la fecha as_of (UTC): libera lo aprobado hasta esa fecha.
        Si llega monthly_budget_usd, lo guarda en la misma escritura."""
        ...

    async def set_monthly_budget(self, company_id: str, monthly_budget_usd: float) -> TreasuryStatus:
        """Cambia solo el presupuesto: no mueve la foto ni el saldo y nunca crea la fila
        (TreasuryNotInitializedError si no existe)."""
        ...


class NotificationPort(Protocol):
    """Avisa al canal de origen el dictamen (sin botones: la aprobación humana se hace en el dashboard)."""

    async def notify_received(self, invoice_channel: str, chat_id: Optional[int]) -> None: ...

    async def notify_decision(self, invoice: ProcessedInvoice) -> None: ...


class IngestionLog(Protocol):
    """Registro de entregas por canal: cada (canal, id externo) se procesa una sola vez."""

    async def claim(self, channel: str, external_id: str) -> Optional[IngestionRecord]:
        """Reclama la entrega de forma atómica. None si este llamado la ganó; si no, el registro existente."""
        ...

    async def complete(self, channel: str, external_id: str, invoice_id: int) -> None: ...

    async def release(self, channel: str, external_id: str) -> None:
        """Libera un reclamo en proceso (falla) para que el reintento sí procese."""
        ...
