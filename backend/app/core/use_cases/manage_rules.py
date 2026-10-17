"""Casos de Uso: Consultar y actualizar las reglas corporativas desde el Dashboard."""

from dataclasses import replace
from typing import Any, Dict

from app.core.domain.errors import InvalidRulesError
from app.core.domain.models import CompanyRules
from app.core.ports.outbound import RulesRepository


class GetRulesUseCase:
    def __init__(self, rules: RulesRepository, company_id: str):
        self.rules = rules
        self.company_id = company_id

    async def execute(self) -> CompanyRules:
        return await self.rules.get(self.company_id)


class UpdateRulesUseCase:
    def __init__(self, rules: RulesRepository, company_id: str):
        self.rules = rules
        self.company_id = company_id

    async def execute(self, changes: Dict[str, Any]) -> CompanyRules:
        """Aplica solo los campos enviados (None se ignora) y valida las reglas ya combinadas:
        un cambio parcial solo puede compararse contra lo guardado."""
        current = await self.rules.get(self.company_id)
        updates = {k: v for k, v in changes.items() if v is not None and hasattr(current, k)}
        merged = replace(current, **updates)
        if merged.max_payment_usd < merged.max_autonomous_usd:
            # Se señala el campo que cambió de verdad, el que hay que corregir: el dashboard envía todas
            # las reglas en cada guardado, así que estar en la solicitud no basta
            changed = {k for k, v in updates.items() if v != getattr(current, k)}
            field = "max_autonomous_usd" if changed & {"max_autonomous_usd", "max_payment_usd"} == {"max_autonomous_usd"} \
                else "max_payment_usd"
            raise InvalidRulesError(field, f"El tope por pago (${merged.max_payment_usd:,.2f}) no puede ser menor "
                                           f"que el umbral de aprobación autónoma (${merged.max_autonomous_usd:,.2f}).")
        return await self.rules.save(merged)
