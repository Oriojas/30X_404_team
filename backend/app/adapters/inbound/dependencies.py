"""
Inyección de dependencias de FastAPI para los adaptadores de entrada.
Es el único punto de los adaptadores que conoce el composition root (app.state.container):
los routers reciben casos de uso del Core, nunca el contenedor.
"""

from typing import Any, Dict, Optional

from fastapi import Request

from app.core.use_cases import (
    DecideInvoiceUseCase,
    GetRulesUseCase,
    GetTreasuryUseCase,
    ListInvoicesUseCase,
    ProcessInvoiceUseCase,
    UpdateRulesUseCase,
)


def get_process_invoice(request: Request) -> ProcessInvoiceUseCase:
    return request.app.state.container.process_invoice


def get_decide_invoice(request: Request) -> DecideInvoiceUseCase:
    return request.app.state.container.decide_invoice


def get_list_invoices(request: Request) -> ListInvoicesUseCase:
    return request.app.state.container.list_invoices


def get_get_rules(request: Request) -> GetRulesUseCase:
    return request.app.state.container.get_rules


def get_get_treasury(request: Request) -> GetTreasuryUseCase:
    return request.app.state.container.get_treasury


def get_update_rules(request: Request) -> UpdateRulesUseCase:
    return request.app.state.container.update_rules


def get_telegram_file_source(request: Request):
    """Entrega la implementación de TelegramFileSource armada en el composition root."""
    return request.app.state.container.telegram


def get_telegram_webhook_secret(request: Request) -> Optional[str]:
    return request.app.state.container.settings.telegram_webhook_secret


def get_system_status(request: Request) -> Dict[str, Any]:
    return request.app.state.container.status()
