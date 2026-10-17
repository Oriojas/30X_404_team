"""
Caso de Uso: Procesar Factura
Orquesta OCR -> FX Engine -> Tubería de Reglas -> Audit Log -> Persistencia -> Notificación.
Lo invocan los adaptadores de entrada (API REST, Telegram) sin conocer los detalles de salida.

Idempotencia en dos niveles:
- Transporte: con external_id (update_id, Idempotency-Key) cada entrega se procesa una sola vez.
- Negocio: un archivo idéntico (SHA-256) a una factura vigente no pasa por el OCR y se rechaza por INTEG-01.
"""

import asyncio
import hashlib
from typing import Awaitable, Callable, Optional, Tuple

from app.core.domain.audit_logger import AuditLogger
from app.core.domain.fx_converter import FXConverter
from app.core.domain.models import CompanyRules, ExtractedInvoice, IngestionResult, ProcessedInvoice
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
        solvency_lock: Optional[asyncio.Lock] = None,
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
        # Compartido con DecideInvoiceUseCase y el PATCH de tesorería (una instancia en container.py):
        # dos evaluaciones no leen el mismo disponible. Vale con una sola réplica del backend.
        self.solvency_lock = solvency_lock or asyncio.Lock()

    async def from_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        channel_source: str,
        chat_id: Optional[int] = None,
        external_id: Optional[str] = None,
    ) -> IngestionResult:
        """Procesa un documento (foto/PDF) recibido por un canal de ingesta."""

        async def load_file() -> bytes:
            return file_bytes

        return await self.from_remote_document(load_file, mime_type, channel_source, chat_id, external_id)

    async def from_remote_document(
        self,
        load_file: Callable[[], Awaitable[bytes]],
        mime_type: str,
        channel_source: str,
        chat_id: Optional[int] = None,
        external_id: Optional[str] = None,
    ) -> IngestionResult:
        """Como from_document, pero el archivo se descarga solo si la entrega no es una repetición."""

        async def work() -> ProcessedInvoice:
            if self.notifier:
                await self.notifier.notify_received(channel_source, chat_id)
            file_bytes = await load_file()
            company_rules = await self.rules.get(self.company_id)
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
            original = await self.invoices.find_by_file_hash(file_sha256, company_rules.duplicate_check_days)
            if original:
                # Mismo archivo que una factura vigente: se reutiliza su lectura en vez de volver a llamar al OCR
                extracted = self._extraction_of(original)
            else:
                extracted = await self.ocr.extract_invoice_data(file_bytes, mime_type)
            return await self._evaluate(
                extracted, channel_source, chat_id, company_rules,
                file_sha256=file_sha256, duplicate_of=original.id if original else None,
            )

        return await self._idempotent(channel_source, external_id, work)

    async def from_extracted(
        self,
        invoice: ExtractedInvoice,
        channel_source: str,
        chat_id: Optional[int] = None,
        external_id: Optional[str] = None,
        ingestion_channel: Optional[str] = None,
    ) -> IngestionResult:
        """Procesa datos de factura ya estructurados (OCR o carga manual).
        ingestion_channel separa el espacio de claves cuando channel_source lo elige el cliente."""

        async def work() -> ProcessedInvoice:
            company_rules = await self.rules.get(self.company_id)
            return await self._evaluate(invoice, channel_source, chat_id, company_rules)

        return await self._idempotent(ingestion_channel or channel_source, external_id, work)

    async def _idempotent(
        self, channel: str, external_id: Optional[str], work: Callable[[], Awaitable[ProcessedInvoice]]
    ) -> IngestionResult:
        """Reclama (canal, external_id) antes de procesar; una repetición devuelve la factura original sin avisos.
        El dictamen se avisa después de marcar la entrega como completada: si el aviso falla, el reintento
        no crea una segunda factura."""
        claimed = bool(self.ingestion and external_id)
        if claimed:
            existing = await self.ingestion.claim(channel, external_id)
            if existing:
                invoice = await self.invoices.get(existing.invoice_id) if existing.invoice_id else None
                return IngestionResult(invoice=invoice, duplicate=True)

        try:
            saved = await work()
        except BaseException:
            # Libera la clave (también si la solicitud se cancela) para que el reintento del canal sí se procese
            if claimed:
                await self.ingestion.release(channel, external_id)
            raise
        if claimed:
            await self.ingestion.complete(channel, external_id, saved.id)

        if self.notifier:
            await self.notifier.notify_decision(saved)
        return IngestionResult(invoice=saved)

    async def _evaluate(
        self,
        invoice: ExtractedInvoice,
        channel_source: str,
        chat_id: Optional[int],
        company_rules: CompanyRules,
        file_sha256: Optional[str] = None,
        duplicate_of: Optional[int] = None,
    ) -> ProcessedInvoice:
        usd_amount, fx_rate = await self._convert_to_usd(invoice)
        # Desde la lectura de la tesorería hasta guardar el dictamen (el OCR queda fuera del candado)
        async with self.solvency_lock:
            context = await self._build_context(invoice, usd_amount, fx_rate, company_rules.duplicate_check_days)
            if duplicate_of is not None:
                context.is_duplicate = True
                context.duplicate_of_invoice_id = duplicate_of

            decision = self.pipeline.evaluate_invoice(invoice, context, company_rules)
            # Sin conversión se registra 0 USD y tasa nula; la explicación (INTEG-04) muestra el monto original
            processed = AuditLogger.build_processed_invoice(
                invoice, context.usd_amount, fx_rate, decision, channel_source, chat_id
            )
            processed.file_sha256 = file_sha256
            return await self.invoices.save(processed)

    @staticmethod
    def _extraction_of(invoice: ProcessedInvoice) -> ExtractedInvoice:
        return ExtractedInvoice(
            invoice_number=invoice.invoice_number,
            vendor_name=invoice.vendor_name,
            original_amount=invoice.original_amount,
            original_currency=invoice.original_currency,
            vendor_tax_id=invoice.vendor_tax_id,
            bank_account=invoice.bank_account,
            due_date=invoice.due_date,
            ocr_confidence_score=invoice.ocr_confidence_score or 0.0,
        )

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
        vendor, sanctions_match, treasury = await asyncio.gather(
            self.vendors.find(invoice.vendor_tax_id, invoice.vendor_name),
            self.sanctions.find_match(invoice.vendor_name, invoice.vendor_tax_id, invoice.bank_account),
            self.treasury.get(self.company_id),
        )

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
