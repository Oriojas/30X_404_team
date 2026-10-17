"""Endpoints REST de reglas y umbrales corporativos."""

from fastapi import APIRouter, Depends

from app.adapters.inbound.api.schemas import CompanyRulesResponse, CompanyRulesUpdate
from app.adapters.inbound.dependencies import get_get_rules, get_update_rules
from app.core.use_cases import GetRulesUseCase, UpdateRulesUseCase

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=CompanyRulesResponse)
async def get_rules(use_case: GetRulesUseCase = Depends(get_get_rules)):
    """Consulta las reglas y umbrales vigentes para la empresa."""
    return CompanyRulesResponse.from_domain(await use_case.execute())


@router.post("", response_model=CompanyRulesResponse)
async def update_rules(payload: CompanyRulesUpdate, use_case: UpdateRulesUseCase = Depends(get_update_rules)):
    """Actualiza los umbrales autónomos y políticas desde el Dashboard."""
    return CompanyRulesResponse.from_domain(await use_case.execute(payload.model_dump()))
