"""Casos de Uso: consultar la liquidez de la cuenta Blinka (saldo, comprometido, presupuesto y gasto del mes)
y tomar una foto nueva del saldo."""

import asyncio
from datetime import datetime
from typing import Optional

from app.core.domain.models import TreasuryStatus
from app.core.ports.outbound import TreasuryRepository


class GetTreasuryUseCase:
    def __init__(self, treasury: TreasuryRepository, company_id: str):
        self.treasury = treasury
        self.company_id = company_id

    async def execute(self) -> TreasuryStatus:
        return await self.treasury.get(self.company_id)


class UpdateTreasuryBalanceUseCase:
    """Registra el saldo vigente como foto nueva: lo aprobado antes deja de comprometerlo."""

    def __init__(self, treasury: TreasuryRepository, company_id: str, solvency_lock: Optional[asyncio.Lock] = None):
        self.treasury = treasury
        self.company_id = company_id
        self.solvency_lock = solvency_lock or asyncio.Lock()

    async def execute(self, balance_usd: float) -> TreasuryStatus:
        async with self.solvency_lock:
            return await self._set_balance(balance_usd)

    async def _set_balance(self, balance_usd: float) -> TreasuryStatus:
        # Mismo reloj que processed_at y decided_at (la app, en UTC): con el de la base, una aprobación
        # de milisegundos antes podría quedar después de la foto si los relojes no coinciden.
        return await self.treasury.set_balance(self.company_id, balance_usd, datetime.utcnow())
