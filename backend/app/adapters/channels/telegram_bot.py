"""
Adaptador de Canal: Bot de Telegram
Maneja la recepción de adjuntos (fotos/PDFs) vía Webhooks y el envío de notificaciones/botones HITL.
"""

import os
from typing import Dict, Any, Optional


class TelegramChannelAdapter:
    """Adaptador para la interacción con la API de Telegram."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")

    async def process_incoming_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una actualización de Webhook recibida desde Telegram."""
        # TODO: Implementar lógica de extracción de archivo y mensaje
        return {"status": "received", "data": update_data}

    async def send_decision_notification(
        self, chat_id: int, decision: str, explanation: str, invoice_id: str
    ) -> bool:
        """Envía el resultado de la evaluación al usuario con opciones interactivas."""
        # TODO: Implementar envío de mensaje con Inline Keyboard para SCALED_TO_HUMAN
        return True
