"""
Adaptador de Salida: Cliente de la API de Telegram
Implementa NotificationPort (dictamen + botones HITL) y descarga los adjuntos recibidos por el webhook.
"""

from typing import Optional

from ....core.domain.models import ProcessedInvoice


class TelegramClient:
    """Adaptador para la interacción con la API de Telegram."""

    def __init__(self, bot_token: Optional[str]):
        self.bot_token = bot_token

    async def download_file(self, file_id: str) -> bytes:
        """Descarga una foto o PDF enviado por el usuario."""
        # TODO: Implementar getFile + descarga con httpx
        return b""

    async def send_decision(self, chat_id: int, invoice: ProcessedInvoice) -> bool:
        """Envía el resultado de la evaluación al usuario con opciones interactivas."""
        # TODO: Implementar envío de mensaje con Inline Keyboard para SCALED_TO_HUMAN
        return True
