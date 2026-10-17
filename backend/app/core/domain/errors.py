"""Errores de negocio que los adaptadores de entrada traducen a respuestas (HTTP, Telegram)."""


class DomainError(Exception):
    """Base de los errores del Core."""


class NotFoundError(DomainError):
    """El recurso pedido no existe (HTTP 404)."""


class ConflictError(DomainError):
    """La operación choca con el estado actual del recurso (HTTP 409)."""


class InvoiceNotFoundError(NotFoundError):
    def __init__(self, invoice_id: int):
        super().__init__(f"La factura {invoice_id} no existe.")


class UnconvertedAmountApprovalError(ConflictError):
    """INTEG-04: sin conversión a USD, aprobar comprometería $0 por un monto real desconocido."""

    def __init__(self, invoice_id: int):
        super().__init__(
            f"La factura {invoice_id} no tiene conversión a USD (INTEG-04): no se puede aprobar porque se "
            "desconoce cuánto comprometería de la tesorería. Solo se puede rechazar."
        )


class InvalidDecisionStateError(ConflictError):
    def __init__(self, invoice_id: int, status: str):
        super().__init__(
            f"La factura {invoice_id} está en estado {status}; solo se pueden decidir facturas en SCALED_TO_HUMAN."
        )
