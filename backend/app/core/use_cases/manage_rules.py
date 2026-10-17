"""Casos de Uso: Consultar y actualizar las reglas corporativas desde el Dashboard."""

from dataclasses import replace
from typing import Any, Dict

from ..domain.models import CompanyRules
from ..ports.outbound import RulesRepository


class GetRulesUseCase:
    def __init__(self, rules: RulesRepository, company_id: str = "BLINKA_DEFAULT"):
        self.rules = rules
        self.company_id = company_id

    async def execute(self) -> CompanyRules:
        return await self.rules.get(self.company_id)


class UpdateRulesUseCase:
    def __init__(self, rules: RulesRepository, company_id: str = "BLINKA_DEFAULT"):
        self.rules = rules
        self.company_id = company_id

    async def execute(self, changes: Dict[str, Any]) -> CompanyRules:
        """Aplica solo los campos enviados (None se ignora)."""
        current = await self.rules.get(self.company_id)
        updates = {k: v for k, v in changes.items() if v is not None and hasattr(current, k)}
        return await self.rules.save(replace(current, **updates))
