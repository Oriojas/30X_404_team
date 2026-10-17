"""Endpoints REST de reglas y umbrales corporativos."""

from fastapi import APIRouter, Depends

from .....container import Container
from ..dependencies import get_container
from ..schemas import CompanyRulesResponse, CompanyRulesUpdate

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=CompanyRulesResponse)
async def get_rules(container: Container = Depends(get_container)):
    """Consulta las reglas y umbrales vigentes para la empresa."""
    return CompanyRulesResponse.from_domain(await container.get_rules.execute())


@router.post("", response_model=CompanyRulesResponse)
async def update_rules(payload: CompanyRulesUpdate, container: Container = Depends(get_container)):
    """Actualiza los umbrales autónomos y políticas desde el Dashboard."""
    rules = await container.update_rules.execute(payload.model_dump())
    return CompanyRulesResponse.from_domain(rules)
