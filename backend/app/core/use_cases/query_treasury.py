"""Caso de Uso: Consultar la liquidez de la cuenta Blinka (saldo, presupuesto y gasto del mes)."""

from app.core.domain.models import TreasuryStatus
from app.core.ports.outbound import TreasuryRepository


class GetTreasuryUseCase:
    def __init__(self, treasury: TreasuryRepository, company_id: str):
        self.treasury = treasury
        self.company_id = company_id

    async def execute(self) -> TreasuryStatus:
        return await self.treasury.get(self.company_id)
