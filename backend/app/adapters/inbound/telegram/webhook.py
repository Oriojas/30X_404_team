"""
Adaptador de Entrada: Webhook de Telegram
Recibe updates con fotos/PDFs, descarga el adjunto y lo entrega al caso de uso ProcessInvoice.
"""

from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, Request

from ....container import Container
from ..api.dependencies import get_container

router = APIRouter(prefix="/api/webhook", tags=["telegram"])


def extract_attachment(update: Dict[str, Any]) -> Optional[Tuple[int, str, str]]:
    """Retorna (chat_id, file_id, mime_type) si el mensaje trae foto o documento."""
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    if chat_id is None:
        return None
    if message.get("photo"):
        return chat_id, message["photo"][-1]["file_id"], "image/jpeg"
    document = message.get("document")
    if document:
        return chat_id, document["file_id"], document.get("mime_type", "application/pdf")
    return None


@router.post("/telegram")
async def telegram_webhook(request: Request, container: Container = Depends(get_container)):
    """Webhook para ingesta de fotos y mensajes desde Telegram."""
    update = await request.json()
    attachment = extract_attachment(update)
    if attachment is None:
        # TODO: Manejar callback_query de los botones HITL y mensajes de texto
        return {"status": "ignored"}

    chat_id, file_id, mime_type = attachment
    file_bytes = await container.telegram.download_file(file_id)
    processed = await container.process_invoice.from_document(
        file_bytes, mime_type, channel_source="TELEGRAM", chat_id=chat_id
    )
    return {"status": "processed", "decision": processed.decision_status.value}
