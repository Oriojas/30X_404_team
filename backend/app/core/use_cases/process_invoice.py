"""
Caso de Uso: Procesar Factura
Orquesta OCR -> FX Engine -> Tubería de Reglas -> Audit Log -> Persistencia -> Notificación.
Lo invocan los adaptadores de entrada (API REST, Telegram) sin conocer los detalles de salida.
"""

import asyncio
from datetime import datetime
from typing import Optional, Tuple

from app.core.domain.audit_logger import AuditLogger
from app.core.domain.fx_converter import FXConverter
from app.core.domain.models import ExtractedInvoice, ProcessedInvoice
from app.core.domain.rules_pipeline import EvaluationContext, RulesPipeline
from app.core.ports.outbound import (
    FXRateProvider,
    IngestionLog,
    InvoiceRepository,
    NotificationPort,
    OCRPort,
    RulesRepository,
    SanctionsRepository,
    TreasuryRepository,
    VendorRepository,
)


class ProcessInvoiceUseCase:
    def __init__(
        self,
        ocr: OCRPort,
        fx_rates: FXRateProvider,
        pipeline: RulesPipeline,
        invoices: InvoiceRepository,
        rules: RulesRepository,
        vendors: VendorRepository,
        sanctions: SanctionsRepository,
        treasury: TreasuryRepository,
        company_id: str,
        notifier: Optional[NotificationPort] = None,
        ingestion: Optional[IngestionLog] = None,
    ):
        self.ocr = ocr
        self.fx_rates = fx_rates
        self.pipeline = pipeline
        self.invoices = invoices
        self.rules = rules
        self.vendors = vendors
        self.sanctions = sanctions
        self.treasury = treasury
        self.company_id = company_id
        self.notifier = notifier
        self.ingestion = ingestion

    async def from_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        channel_source: str,
        chat_id: Optional[int] = None,
    ) -> ProcessedInvoice:
        """Procesa un documento (foto/PDF) recibido por un canal de ingesta."""
        if self.notifier:
            await self.notifier.notify_received(channel_source, chat_id)
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
        usd_amount, fx_rate = await self._convert_to_usd(invoice)
        context = await self._build_context(invoice, usd_amount, fx_rate, company_rules.duplicate_check_days)

        decision = self.pipeline.evaluate_invoice(invoice, context, company_rules)
        # Sin conversión se registra 0 USD y tasa nula; la explicación (INTEG-04) muestra el monto original
        processed = AuditLogger.build_processed_invoice(
            invoice, context.usd_amount, fx_rate, decision, channel_source, chat_id
        )
        saved = await self.invoices.save(processed)

        if self.notifier:
            await self.notifier.notify_decision(saved)
        return saved

    async def _convert_to_usd(self, invoice: ExtractedInvoice) -> Tuple[Optional[float], Optional[float]]:
        """Retorna (usd_amount, fx_rate); (None, None) si la moneda no está soportada."""
        currency = FXConverter.normalize_currency(invoice.original_currency)
        if currency == FXConverter.BASE_CURRENCY:
            return round(invoice.original_amount, 2), 1.0
        rate = await self.fx_rates.get_rate_to_usd(currency)
        if rate is None:
            return None, None
        return FXConverter.to_usd(invoice.original_amount, rate), rate

    async def _build_context(
        self, invoice: ExtractedInvoice, usd_amount: Optional[float], fx_rate: Optional[float], duplicate_days: int
    ) -> EvaluationContext:
        """Reúne vía puertos los hechos externos que necesita la tubería (consultas independientes en paralelo)."""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        vendor, sanctions_match, treasury, month_spent = await asyncio.gather(
            self.vendors.find(invoice.vendor_tax_id, invoice.vendor_name),
            self.sanctions.find_match(invoice.vendor_name, invoice.vendor_tax_id, invoice.bank_account),
            self.treasury.get(self.company_id),
            self.invoices.sum_approved_usd_since(month_start),
        )
        treasury.month_spent_usd = month_spent

        # Las consultas de historial usan la identidad del registro si el proveedor existe
        tax_id = vendor.tax_id if vendor else invoice.vendor_tax_id
        name = vendor.legal_name if vendor else invoice.vendor_name
        # Sin monto válido (moneda no soportada u OCR vacío) no se compara por monto
        comparable_amount = usd_amount if usd_amount and usd_amount > 0 else None
        is_duplicate, has_history = await asyncio.gather(
            self.invoices.exists_duplicate(tax_id, name, invoice.invoice_number, comparable_amount, duplicate_days),
            self.invoices.vendor_has_paid_history(tax_id, name),
        )

        return EvaluationContext(
            usd_amount=usd_amount or 0.0,
            fx_rate=fx_rate or 0.0,
            currency_supported=usd_amount is not None,
            treasury=treasury,
            vendor=vendor,
            sanctions_match=sanctions_match,
            is_duplicate=is_duplicate,
            vendor_has_history=has_history,
        )
