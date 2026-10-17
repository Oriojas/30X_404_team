"""
Adaptador de Entrada: Webhook de Telegram
Recibe updates con fotos/PDFs, descarga el adjunto y lo entrega al caso de uso ProcessInvoice.
Telegram es solo canal de ingesta: la aprobación de facturas escaladas se hace en el dashboard.

Seguridad: Telegram firma cada llamada con el header X-Telegram-Bot-Api-Secret-Token (configurado en
setWebhook con secret_token). Sin TELEGRAM_WEBHOOK_SECRET el webhook queda deshabilitado (falla cerrado).
"""

import hmac
from typing import Any, Dict, Optional, Protocol, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.adapters.inbound.dependencies import (
    get_process_invoice,
    get_telegram_file_source,
    get_telegram_webhook_secret,
)
from app.core.use_cases import ProcessInvoiceUseCase

router = APIRouter(prefix="/api/webhook", tags=["telegram"])


class TelegramFileSource(Protocol):
    """Lo único que el webhook necesita del canal: descargar el adjunto por file_id."""

    async def download_file(self, file_id: str) -> bytes: ...


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


def verify_secret(
    secret: Optional[str] = Depends(get_telegram_webhook_secret),
    received: Optional[str] = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> None:
    if not secret:
        raise HTTPException(503, "Webhook de Telegram deshabilitado: configura TELEGRAM_WEBHOOK_SECRET.")
    if not received or not hmac.compare_digest(received, secret):
        raise HTTPException(401, "Secret token de Telegram inválido.")


@router.post("/telegram", dependencies=[Depends(verify_secret)])
async def telegram_webhook(
    request: Request,
    use_case: ProcessInvoiceUseCase = Depends(get_process_invoice),
    files: TelegramFileSource = Depends(get_telegram_file_source),
):
    """Webhook para ingesta de fotos y mensajes desde Telegram."""
    update = await request.json()
    attachment = extract_attachment(update)
    if attachment is None:
        # Mensajes sin adjunto (texto, stickers, etc.) no inician el flujo
        return {"status": "ignored"}

    chat_id, file_id, mime_type = attachment
    file_bytes = await files.download_file(file_id)
    result = await use_case.from_document(
        file_bytes, mime_type, channel_source="TELEGRAM", chat_id=chat_id
    )
    return {"status": "processed", "decision": result.invoice.decision_status.value}
