"""
Módulo Core: Conversión de Divisas (FX Engine)
Normaliza montos multidivisa (COP, MXN, EUR, BRL, ARS) a USD equivalente a $0.00 FX Markup.
La tasa la provee un FXRateProvider (puerto); este módulo solo aplica el cálculo.
"""

from typing import Tuple

from ..ports.outbound import FXRateProvider


class FXConverter:
    """Motor de normalización y conversión de divisas."""

    BLINKA_FX_MARKUP_USD = 0.00

    def __init__(self, rate_provider: FXRateProvider):
        self.rate_provider = rate_provider

    async def convert_to_usd(self, amount: float, currency: str) -> Tuple[float, float]:
        """
        Convierte un monto en moneda local a USD aplicando la tasa vigente.
        Retorna (usd_amount, fx_rate_applied).
        """
        curr = currency.upper().strip()
        if curr == "USD":
            return round(amount, 2), 1.0

        rate = await self.rate_provider.get_rate_to_usd(curr)
        usd_value = round(amount / rate + self.BLINKA_FX_MARKUP_USD, 2)
        return usd_value, rate
