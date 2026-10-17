"""
Adaptador de Salida: Tasas de Cambio de Referencia
Implementa FXRateProvider con tasas fijas; puede reemplazarse por un proveedor en vivo sin tocar el Core.
"""


class StaticFXRateProvider:
    """Tasas de referencia iniciales (unidades de moneda local por 1 USD)."""

    DEFAULT_RATES_TO_USD = {
        "USD": 1.0,
        "COP": 4200.0,
        "MXN": 19.50,
        "EUR": 0.92,
        "BRL": 5.60,
        "ARS": 980.0
    }

    async def get_rate_to_usd(self, currency: str) -> float:
        return self.DEFAULT_RATES_TO_USD.get(currency.upper().strip(), 1.0)
