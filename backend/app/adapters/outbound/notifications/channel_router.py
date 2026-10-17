"""
Adaptador de Salida: Router de Notificaciones por Canal
Implementa NotificationPort y delega en el notificador del canal de origen de la factura.
Agregar un canal (email, WhatsApp) es registrar su notificador en container.py; los canales sin
notificador (WEB, API) simplemente no reciben aviso.
"""

from typing import Mapping, Optional

from app.core.domain.models import ProcessedInvoice
from app.core.ports.outbound import NotificationPort


class ChannelNotificationRouter:
    def __init__(self, notifiers: Mapping[str, NotificationPort]):
        self.notifiers = dict(notifiers)

    async def notify_received(self, invoice_channel: str, chat_id: Optional[int]) -> None:
        notifier = self.notifiers.get(invoice_channel)
        if notifier:
            await notifier.notify_received(invoice_channel, chat_id)

    async def notify_decision(self, invoice: ProcessedInvoice) -> None:
        notifier = self.notifiers.get(invoice.channel_source)
        if notifier:
            await notifier.notify_decision(invoice)
