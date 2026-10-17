"""Puertos: contratos que el Core exige a los adaptadores de salida."""

from app.core.ports.outbound import (
    FXRateProvider,
    InvoiceRepository,
    NotificationPort,
    OCRPort,
    RulesRepository,
    SanctionsRepository,
    TreasuryRepository,
    VendorRepository,
)

__all__ = [
    "FXRateProvider",
    "InvoiceRepository",
    "NotificationPort",
    "OCRPort",
    "RulesRepository",
    "SanctionsRepository",
    "TreasuryRepository",
    "VendorRepository",
]
