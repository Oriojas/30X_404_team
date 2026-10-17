"""
Módulo Core: Conversión de Divisas (FX Engine)
Normaliza montos multidivisa (COP, MXN, EUR, BRL, ARS) a USD equivalente a $0.00 FX Markup.
Cálculo puro: la tasa la obtiene el caso de uso a través del puerto FXRateProvider.
"""


class FXConverter:
    """Motor de normalización y conversión de divisas."""

    BASE_CURRENCY = "USD"
    BLINKA_FX_MARKUP_USD = 0.00

    @staticmethod
    def normalize_currency(currency: str) -> str:
        return (currency or "").upper().strip()

    @classmethod
    def to_usd(cls, amount: float, rate_to_usd: float) -> float:
        """Convierte con una tasa expresada en unidades de moneda local por 1 USD."""
        return round(amount / rate_to_usd + cls.BLINKA_FX_MARKUP_USD, 2)
