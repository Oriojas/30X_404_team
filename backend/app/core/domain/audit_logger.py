"""
Módulo Core: Generador de Audit Log & Explicabilidad en Lenguaje Natural
Construye la factura procesada con su explicación para el Dashboard web y los canales de ingesta.
"""

from typing import Optional

from app.core.domain.models import Decision, ExtractedInvoice, ProcessedInvoice


class AuditLogger:
    """Generador de registros de auditoría y explicabilidad."""

    @staticmethod
    def build_processed_invoice(
        invoice: ExtractedInvoice,
        usd_amount: float,
        fx_rate: Optional[float],
        decision: Decision,
        channel_source: str,
        source_chat_id: Optional[int] = None,
    ) -> ProcessedInvoice:
        """Construye la entidad de trazabilidad completa."""
        return ProcessedInvoice(
            invoice_number=invoice.invoice_number or "SIN_NUMERO",
            vendor_name=invoice.vendor_name or "PROVEEDOR_DESCONOCIDO",
            vendor_tax_id=invoice.vendor_tax_id,
            bank_account=invoice.bank_account,
            original_amount=invoice.original_amount,
            original_currency=invoice.original_currency.upper(),
            usd_amount=usd_amount,
            fx_rate_applied=fx_rate,
            due_date=invoice.due_date,
            ocr_confidence_score=invoice.ocr_confidence_score,
            channel_source=channel_source,
            source_chat_id=source_chat_id,
            decision_status=decision.status,
            audit_explanation=decision.explanation,
            evaluations=decision.evaluations,
        )
