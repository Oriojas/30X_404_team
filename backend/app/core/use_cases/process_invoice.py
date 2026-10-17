"""
Caso de Uso: Procesar Factura
Orquesta OCR -> FX Engine -> Tubería de Reglas -> Audit Log -> Persistencia -> Notificación.
Lo invocan los adaptadores de entrada (API REST, Telegram) sin conocer los detalles de salida.
"""

from typing import Optional

from ..domain.audit_logger import AuditLogger
from ..domain.fx_converter import FXConverter
from ..domain.models import ExtractedInvoice, ProcessedInvoice
from ..domain.rules_pipeline import EvaluationContext, RulesPipeline
from ..ports.outbound import InvoiceRepository, NotificationPort, OCRPort, RulesRepository

class ProcessInvoiceUseCase:
    def __init__(
        self,
        ocr: OCRPort,
        fx_converter: FXConverter,
        pipeline: RulesPipeline,
        invoices: InvoiceRepository,
        rules: RulesRepository,
        notifier: Optional[NotificationPort] = None,
        company_id: str = "BLINKA_DEFAULT",
    ):
        self.ocr = ocr
        self.fx_converter = fx_converter
        self.pipeline = pipeline
        self.invoices = invoices
        self.rules = rules
        self.notifier = notifier
        self.company_id = company_id

    async def from_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        channel_source: str,
        chat_id: Optional[int] = None,
    ) -> ProcessedInvoice:
        """Procesa un documento (foto/PDF) recibido por un canal de ingesta."""
        extracted = await self.ocr.extract_invoice_data(file_bytes, mime_type)
        return await self.from_extracted(extracted, channel_source, chat_id)

    async def from_extracted(
        self,
        invoice: ExtractedInvoice,
        channel_source: str,
        chat_id: Optional[int] = None,
    ) -> ProcessedInvoice:
        """Procesa datos de factura ya estructurados (OCR o carga manual)."""
        company_rules = await self.rules.get(self.company_id)
        usd_amount, fx_rate = await self.fx_converter.convert_to_usd(
            invoice.original_amount, invoice.original_currency
        )
        is_duplicate = await self.invoices.exists_duplicate(
            invoice.vendor_tax_id, invoice.invoice_number, company_rules.duplicate_check_days
        )

        decision = self.pipeline.evaluate_invoice(
            invoice, EvaluationContext(usd_amount=usd_amount, is_duplicate=is_duplicate), company_rules
        )
        processed = AuditLogger.build_processed_invoice(
            invoice, usd_amount, fx_rate, decision, channel_source
        )
        saved = await self.invoices.save(processed)

        if self.notifier and chat_id is not None:
            await self.notifier.send_decision(chat_id, saved)
        return saved
