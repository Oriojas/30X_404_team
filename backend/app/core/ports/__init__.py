"""Puertos: contratos que el Core exige a los adaptadores de salida."""

from .outbound import (
    FXRateProvider,
    InvoiceRepository,
    NotificationPort,
    OCRPort,
    RulesRepository,
)

__all__ = [
    "FXRateProvider",
    "InvoiceRepository",
    "NotificationPort",
    "OCRPort",
    "RulesRepository",
]
