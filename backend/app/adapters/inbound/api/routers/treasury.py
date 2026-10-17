"""Endpoints REST de la tesorería Blinka."""

from fastapi import APIRouter, Depends

from app.adapters.inbound.api.schemas import TreasuryBalanceUpdate, TreasuryResponse
from app.adapters.inbound.dependencies import get_get_treasury, get_update_treasury
from app.core.use_cases import GetTreasuryUseCase, UpdateTreasuryBalanceUseCase

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


@router.get("", response_model=TreasuryResponse)
async def get_treasury(use_case: GetTreasuryUseCase = Depends(get_get_treasury)):
    """Saldo de la foto, comprometido, disponible, presupuesto mensual y gasto aprobado del mes."""
    return TreasuryResponse.from_domain(await use_case.execute())


@router.patch("", response_model=TreasuryResponse)
async def update_treasury_balance(
    payload: TreasuryBalanceUpdate, use_case: UpdateTreasuryBalanceUseCase = Depends(get_update_treasury)
):
    """Registra el saldo vigente como foto nueva: lo aprobado antes deja de comprometerlo."""
    return TreasuryResponse.from_domain(await use_case.execute(payload.balance_usd))
