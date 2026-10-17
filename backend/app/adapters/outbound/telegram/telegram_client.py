"""
Adaptador de Salida: Cliente de la API de Telegram
Implementa NotificationPort para el canal TELEGRAM (el ChannelNotificationRouter solo le entrega facturas de
ese canal) y TelegramFileSource para que el webhook descargue los adjuntos.
Telegram es solo canal de ingesta: los mensajes informan el dictamen, sin botones de aprobación
(la decisión humana se toma en el dashboard).
"""

import logging
from typing import Optional

import httpx

from app.core.domain.models import DecisionStatus, ProcessedInvoice

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    DecisionStatus.AUTO_APPROVED: "✅ Pago aprobado automáticamente",
    DecisionStatus.SCALED_TO_HUMAN: "⏳ Escalada a revisión humana en el dashboard",
    DecisionStatus.REJECTED: "⛔ Pago frenado",
    DecisionStatus.HUMAN_APPROVED: "✅ Pago aprobado por un operador",
    DecisionStatus.HUMAN_REJECTED: "⛔ Pago rechazado por un operador",
}


class TelegramClient:
    """Adaptador para la interacción con la API de Telegram."""

    def __init__(self, bot_token: Optional[str], timeout: float = 20.0):
        self.bot_token = bot_token
        self.timeout = timeout

    @property
    def _api(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"

    async def download_file(self, file_id: str) -> bytes:
        """Descarga una foto o PDF enviado por el usuario."""
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado; no se puede descargar el adjunto.")
            return b""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            meta = await client.get(f"{self._api}/getFile", params={"file_id": file_id})
            meta.raise_for_status()
            file_path = meta.json()["result"]["file_path"]
            content = await client.get(f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}")
            content.raise_for_status()
            return content.content

    async def notify_received(self, invoice_channel: str, chat_id: Optional[int]) -> None:
        if chat_id is not None:
            await self._send(chat_id, "📥 Factura recibida. Analizando datos con OCR y evaluando reglas de seguridad...")

    async def notify_decision(self, invoice: ProcessedInvoice) -> None:
        if invoice.source_chat_id is None:
            return
        text = (
            f"{STATUS_LABELS[invoice.decision_status]}\n"
            f"Factura #{invoice.invoice_number} · {invoice.vendor_name}\n"
            f"Monto: ${invoice.usd_amount:,.2f} USD\n\n{invoice.audit_explanation}"
        )
        await self._send(invoice.source_chat_id, text)

    async def _send(self, chat_id: int, text: str) -> None:
        if not self.bot_token:
            logger.info("Telegram deshabilitado (sin token). Mensaje para %s: %s", chat_id, text)
            return
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self._api}/sendMessage", json={"chat_id": chat_id, "text": text})
                response.raise_for_status()
        except httpx.HTTPError:
            # Una falla al notificar no debe revertir la decisión ya registrada en el Audit Log
            logger.exception("No se pudo notificar a Telegram (chat %s).", chat_id)
