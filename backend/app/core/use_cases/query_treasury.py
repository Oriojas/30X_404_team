"""Casos de Uso: consultar la liquidez de la cuenta Blinka (saldo, comprometido, presupuesto y gasto del mes)
tomar una foto nueva del saldo y editar el presupuesto del periodo."""

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
    """Registra el saldo vigente como foto nueva (lo aprobado antes deja de comprometerlo) y/o el presupuesto
    del periodo. El presupuesto solo no mueve la foto: si lo hiciera, liberaría lo comprometido (F7.1)."""

    def __init__(self, treasury: TreasuryRepository, company_id: str, solvency_lock: Optional[asyncio.Lock] = None):
        self.treasury = treasury
        self.company_id = company_id
        self.solvency_lock = solvency_lock or asyncio.Lock()

    async def execute(self, balance_usd: Optional[float] = None,
                      monthly_budget_usd: Optional[float] = None) -> TreasuryStatus:
        async with self.solvency_lock:
            if balance_usd is None:
                return await self.treasury.set_monthly_budget(self.company_id, monthly_budget_usd)
            # Mismo reloj que processed_at y decided_at (la app, en UTC): con el de la base, una aprobación
            # de milisegundos antes podría quedar después de la foto si los relojes no coinciden.
            return await self.treasury.set_balance(self.company_id, balance_usd, datetime.utcnow(),
                                                   monthly_budget_usd)
