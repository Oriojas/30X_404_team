"""
Caso de Uso: Decisión Humana (Human-in-the-Loop)
Un operador aprueba o rechaza desde el dashboard una factura en SCALED_TO_HUMAN.
Los canales de ingesta (Telegram, etc.) solo reciben el aviso del resultado.
"""

from datetime import datetime
from typing import Optional

from app.core.domain.errors import InvalidDecisionStateError, InvoiceNotFoundError
from app.core.domain.models import DecisionStatus, HumanDecision, ProcessedInvoice
from app.core.ports.outbound import InvoiceRepository, NotificationPort


class DecideInvoiceUseCase:
    def __init__(self, invoices: InvoiceRepository, notifier: Optional[NotificationPort] = None):
        self.invoices = invoices
        self.notifier = notifier

    async def execute(
        self, invoice_id: int, decision: HumanDecision, decided_by: str, note: Optional[str] = None
    ) -> ProcessedInvoice:
        invoice = await self.invoices.get(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        if invoice.decision_status != DecisionStatus.SCALED_TO_HUMAN:
            raise InvalidDecisionStateError(invoice_id, invoice.decision_status.value)

        now = datetime.utcnow()
        if decision == HumanDecision.APPROVE:
            status, verb = DecisionStatus.HUMAN_APPROVED, "Aprobado"
        else:
            status, verb = DecisionStatus.HUMAN_REJECTED, "Rechazado"
        explanation = (
            f"{invoice.audit_explanation} | {verb} manualmente por {decided_by} desde el dashboard "
            f"el {now:%Y-%m-%d %H:%M} UTC." + (f" Nota: {note}" if note else "")
        )

        updated = await self.invoices.update_decision(
            invoice_id, status, explanation, decided_by, now, note, expected_status=DecisionStatus.SCALED_TO_HUMAN
        )
        if updated is None:
            # Otro operador la decidió entre la lectura y la escritura
            current = await self.invoices.get(invoice_id)
            raise InvalidDecisionStateError(invoice_id, current.decision_status.value if current else "DESCONOCIDO")
        if self.notifier:
            await self.notifier.notify_decision(updated)
        return updated
