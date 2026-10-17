"""Errores de negocio que los adaptadores de entrada traducen a respuestas (HTTP, Telegram)."""


class DomainError(Exception):
    """Base de los errores del Core."""


class InvoiceNotFoundError(DomainError):
    def __init__(self, invoice_id: int):
        super().__init__(f"La factura {invoice_id} no existe.")


class InvalidDecisionStateError(DomainError):
    def __init__(self, invoice_id: int, status: str):
        super().__init__(
            f"La factura {invoice_id} está en estado {status}; solo se pueden decidir facturas en SCALED_TO_HUMAN."
        )
