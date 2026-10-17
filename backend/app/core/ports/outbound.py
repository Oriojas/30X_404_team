"""
Puertos de Salida
Interfaces que el Core necesita del mundo exterior. Cada adaptador en `adapters/outbound/` implementa una.
"""

from typing import List, Optional, Protocol

from ..domain.models import CompanyRules, ExtractedInvoice, ProcessedInvoice


class OCRPort(Protocol):
    """Extracción estructurada de facturas desde imágenes o PDFs."""

    async def extract_invoice_data(self, file_bytes: bytes, mime_type: str) -> ExtractedInvoice: ...


class FXRateProvider(Protocol):
    """Fuente de tasas de cambio (unidades de moneda local por 1 USD)."""

    async def get_rate_to_usd(self, currency: str) -> float: ...


class InvoiceRepository(Protocol):
    """Persistencia de facturas procesadas y Audit Log."""

    async def save(self, invoice: ProcessedInvoice) -> ProcessedInvoice: ...

    async def list_recent(self, limit: int = 50) -> List[ProcessedInvoice]: ...

    async def exists_duplicate(
        self, vendor_tax_id: Optional[str], invoice_number: Optional[str], within_days: int
    ) -> bool: ...


class RulesRepository(Protocol):
    """Lectura y actualización de reglas corporativas."""

    async def get(self, company_id: str) -> CompanyRules: ...

    async def save(self, rules: CompanyRules) -> CompanyRules: ...


class NotificationPort(Protocol):
    """Envío del dictamen al usuario (con botones HITL cuando aplica)."""

    async def send_decision(self, chat_id: int, invoice: ProcessedInvoice) -> bool: ...
