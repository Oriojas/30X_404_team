"""
Módulo Core: Generador de Audit Log & Explicabilidad en Lenguaje Natural
Construye la factura procesada con su explicación para el Dashboard web y Telegram.
"""

from .models import Decision, ExtractedInvoice, ProcessedInvoice


class AuditLogger:
    """Generador de registros de auditoría y explicabilidad."""

    @staticmethod
    def build_processed_invoice(
        invoice: ExtractedInvoice,
        usd_amount: float,
        fx_rate: float,
        decision: Decision,
        channel_source: str,
    ) -> ProcessedInvoice:
        """Construye la entidad de trazabilidad completa."""
        return ProcessedInvoice(
            invoice_number=invoice.invoice_number or "SIN_NUMERO",
            vendor_name=invoice.vendor_name or "PROVEEDOR_DESCONOCIDO",
            vendor_tax_id=invoice.vendor_tax_id,
            original_amount=invoice.original_amount,
            original_currency=invoice.original_currency,
            usd_amount=usd_amount,
            fx_rate_applied=fx_rate,
            due_date=invoice.due_date,
            channel_source=channel_source,
            decision_status=decision.status,
            audit_explanation=decision.explanation,
            evaluations=decision.evaluations,
        )
