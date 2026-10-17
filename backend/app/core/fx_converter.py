"""
Módulo Core: Conversión de Divisas (FX Engine)
Normaliza montos multidivisa (COP, MXN, EUR, BRL, ARS) a USD equivalente a $0.00 FX Markup.
"""

from typing import Dict, Any, Tuple


class FXConverter:
    """Motor de normalización y conversión de divisas."""

    # Tasas de referencia iniciales (pueden alimentarse dinámicamente o por API)
    DEFAULT_RATES_TO_USD = {
        "USD": 1.0,
        "COP": 4200.0,
        "MXN": 19.50,
        "EUR": 0.92,
        "BRL": 5.60,
        "ARS": 980.0
    }

    def convert_to_usd(self, amount: float, currency: str) -> Tuple[float, float]:
        """
        Convierte un monto en moneda local a USD aplicando la tasa de referencia.
        Retorna (usd_amount, fx_rate_applied).
        """
        curr = currency.upper().strip()
        rate = self.DEFAULT_RATES_TO_USD.get(curr, 1.0)
        
        if curr == "USD":
            return round(amount, 2), 1.0
        
        usd_value = round(amount / rate, 2)
        return usd_value, rate
