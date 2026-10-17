"""
Adaptador de Salida: PostgreSQL
Implementa InvoiceRepository y RulesRepository sobre las tablas `invoices` y `company_rules`.
"""

from typing import List, Optional

from ....core.domain.models import CompanyRules, ProcessedInvoice


class PostgresInvoiceRepository:
    """Repositorio de facturas para PostgreSQL (Railway / Local)."""

    def __init__(self, database_url: Optional[str]):
        self.database_url = database_url

    async def save(self, invoice: ProcessedInvoice) -> ProcessedInvoice:
        """Persiste una factura procesada y la retorna con su ID."""
        # TODO: Implementar inserción mediante SQLAlchemy
        return invoice

    async def list_recent(self, limit: int = 50) -> List[ProcessedInvoice]:
        """Obtiene el historial reciente de facturas y auditoría."""
        # TODO: Implementar consulta a la base de datos
        return []

    async def exists_duplicate(
        self, vendor_tax_id: Optional[str], invoice_number: Optional[str], within_days: int
    ) -> bool:
        """Busca la misma factura (NIT + número) en la ventana de días configurada."""
        # TODO: Implementar consulta usando idx_invoices_vendor_number
        return False


class PostgresRulesRepository:
    """Repositorio de reglas corporativas para PostgreSQL."""

    def __init__(self, database_url: Optional[str], defaults: CompanyRules):
        self.database_url = database_url
        self.defaults = defaults

    async def get(self, company_id: str) -> CompanyRules:
        """Obtiene las reglas configuradas para una empresa."""
        # TODO: Implementar lectura de reglas configurables
        return self.defaults

    async def save(self, rules: CompanyRules) -> CompanyRules:
        """Actualiza las reglas de la empresa."""
        # TODO: Implementar UPDATE sobre company_rules
        self.defaults = rules
        return rules
