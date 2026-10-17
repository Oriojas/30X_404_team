"""Caso de Uso: Consultar la liquidez de la cuenta Blinka (saldo, presupuesto y gasto del mes)."""

from datetime import datetime

from app.core.domain.models import TreasuryStatus
from app.core.ports.outbound import InvoiceRepository, TreasuryRepository


def month_start() -> datetime:
    """Inicio del mes en curso (UTC): ventana del presupuesto mensual (FIN-02)."""
    return datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class GetTreasuryUseCase:
    def __init__(self, treasury: TreasuryRepository, invoices: InvoiceRepository, company_id: str):
        self.treasury = treasury
        self.invoices = invoices
        self.company_id = company_id

    async def execute(self) -> TreasuryStatus:
        status = await self.treasury.get(self.company_id)
        status.month_spent_usd = await self.invoices.sum_approved_usd_since(month_start())
        return status
