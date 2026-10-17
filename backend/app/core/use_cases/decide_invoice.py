"""
Caso de Uso: Decisión Humana (Human-in-the-Loop)
Un operador aprueba o rechaza desde el dashboard una factura en SCALED_TO_HUMAN.
Antes de aprobar se revalida la solvencia con la tesorería y las reglas vigentes. La persona puede aprobar
con alertas FIN que escalan, y el Audit Log las registra como excepción aprobada por ella (F6.3). No puede
aprobar sin conversión a USD (INTEG-04) ni por encima del tope duro por pago (FIN-04, F7.2): solo rechazar.
Los canales de ingesta (Telegram, etc.) solo reciben el aviso del resultado.
"""

import asyncio
from datetime import datetime
from typing import Optional

from app.core.domain.errors import (
    InvalidDecisionStateError,
    InvoiceNotFoundError,
    PaymentCapExceededError,
    UnconvertedAmountApprovalError,
)
from app.core.domain.models import DecisionStatus, HumanDecision, ProcessedInvoice
from app.core.domain.rules_pipeline import RulesPipeline, format_usd
from app.core.ports.outbound import InvoiceRepository, NotificationPort, RulesRepository, TreasuryRepository


class DecideInvoiceUseCase:
    def __init__(
        self,
        invoices: InvoiceRepository,
        treasury: TreasuryRepository,
        rules: RulesRepository,
        company_id: str,
        notifier: Optional[NotificationPort] = None,
        pipeline: Optional[RulesPipeline] = None,
        solvency_lock: Optional[asyncio.Lock] = None,
    ):
        self.invoices = invoices
        self.treasury = treasury
        self.rules = rules
        self.company_id = company_id
        self.notifier = notifier
        self.pipeline = pipeline or RulesPipeline()
        self.solvency_lock = solvency_lock or asyncio.Lock()

    async def execute(
        self, invoice_id: int, decision: HumanDecision, decided_by: str, note: Optional[str] = None
    ) -> ProcessedInvoice:
        # El mismo candado que la ingesta: la revalidación y el guardado ven un disponible estable
        async with self.solvency_lock:
            updated = await self._decide(invoice_id, decision, decided_by, note)
        if self.notifier:
            await self.notifier.notify_decision(updated)
        return updated

    async def _decide(
        self, invoice_id: int, decision: HumanDecision, decided_by: str, note: Optional[str]
    ) -> ProcessedInvoice:
        invoice = await self.invoices.get(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        if invoice.decision_status != DecisionStatus.SCALED_TO_HUMAN:
            raise InvalidDecisionStateError(invoice_id, invoice.decision_status.value)

        if decision == HumanDecision.APPROVE:
            if invoice.usd_amount <= 0:
                raise UnconvertedAmountApprovalError(invoice_id)
            solvency = await self._revalidate_solvency(invoice, decided_by)  # PaymentCapExceededError si FIN-04
            status, verb = DecisionStatus.HUMAN_APPROVED, "Aprobado"
        else:
            solvency = ""
            status, verb = DecisionStatus.HUMAN_REJECTED, "Rechazado"

        now = datetime.utcnow()
        explanation = (
            f"{invoice.audit_explanation} | {verb} manualmente por {decided_by} desde el dashboard "
            f"el {now:%Y-%m-%d %H:%M} UTC." + solvency + (f" Nota: {note}" if note else "")
        )

        updated = await self.invoices.update_decision(
            invoice_id, status, explanation, decided_by, now, note, expected_status=DecisionStatus.SCALED_TO_HUMAN
        )
        if updated is None:
            # Otro operador la decidió entre la lectura y la escritura
            current = await self.invoices.get(invoice_id)
            raise InvalidDecisionStateError(invoice_id, current.decision_status.value if current else "DESCONOCIDO")
        return updated

    async def _revalidate_solvency(self, invoice: ProcessedInvoice, decided_by: str) -> str:
        """Capa 3 con la tesorería y las reglas vigentes; devuelve el texto para el Audit Log."""
        treasury = await self.treasury.get(self.company_id)
        rules = await self.rules.get(self.company_id)
        alerts = self.pipeline.evaluate_solvency(invoice.usd_amount, treasury, rules)
        cap = next((a for a in alerts if a.code == "FIN-04"), None)
        if cap:
            raise PaymentCapExceededError(invoice.id, cap.message)
        summary = f" Solvencia al aprobar: disponible {format_usd(treasury.available_usd)} para un pago de {format_usd(invoice.usd_amount)}"
        if not alerts:
            return summary + ", sin alertas FIN."
        detail = " ".join(f"[{a.code}] {a.message}" for a in alerts)
        return f"{summary}. Excepción aprobada por {decided_by} con alertas FIN vigentes: {detail}"
