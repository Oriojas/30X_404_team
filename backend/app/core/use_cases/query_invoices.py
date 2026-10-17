"""Caso de Uso: Consultar el historial de facturas (Audit Log)."""

from typing import List

from ..domain.models import ProcessedInvoice
from ..ports.outbound import InvoiceRepository


class ListInvoicesUseCase:
    def __init__(self, invoices: InvoiceRepository):
        self.invoices = invoices

    async def execute(self, limit: int = 50) -> List[ProcessedInvoice]:
        return await self.invoices.list_recent(limit)
