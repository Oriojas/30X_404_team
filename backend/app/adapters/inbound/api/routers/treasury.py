"""Endpoint REST de la tesorería Blinka (solo lectura)."""

from fastapi import APIRouter, Depends

from app.adapters.inbound.api.schemas import TreasuryResponse
from app.adapters.inbound.dependencies import get_get_treasury
from app.core.use_cases import GetTreasuryUseCase

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


@router.get("", response_model=TreasuryResponse)
async def get_treasury(use_case: GetTreasuryUseCase = Depends(get_get_treasury)):
    """Saldo, presupuesto mensual y gasto aprobado del mes de la cuenta Blinka."""
    return TreasuryResponse.from_domain(await use_case.execute())
