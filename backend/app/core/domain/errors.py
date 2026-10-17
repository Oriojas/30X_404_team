"""Errores de negocio que los adaptadores de entrada traducen a respuestas (HTTP, Telegram)."""


class DomainError(Exception):
    """Base de los errores del Core."""


class NotFoundError(DomainError):
    """El recurso pedido no existe (HTTP 404)."""


class ConflictError(DomainError):
    """La operación choca con el estado actual del recurso (HTTP 409)."""


class InvalidFieldError(DomainError):
    """Un valor que el Core rechaza (reglas incoherentes entre sí, actualización de tesorería vacía):
    HTTP 422 con el campo que hay que corregir."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


class InvoiceNotFoundError(NotFoundError):
    def __init__(self, invoice_id: int):
        super().__init__(f"La factura {invoice_id} no existe.")


class VendorNotFoundError(NotFoundError):
    def __init__(self, vendor_id: int):
        super().__init__(f"El beneficiario {vendor_id} no existe.")


class VendorAlreadyExistsError(ConflictError):
    """NIT o razón social ya registrados: find() empata por cualquiera de los dos."""

    def __init__(self, field: str, value: str):
        label = "NIT" if field == "tax_id" else "razón social"
        super().__init__(f"Ya existe un beneficiario con {label} {value}.")
        self.field = field


class UnconvertedAmountApprovalError(ConflictError):
    """INTEG-04: sin conversión a USD, aprobar comprometería $0 por un monto real desconocido."""

    def __init__(self, invoice_id: int):
        super().__init__(
            f"La factura {invoice_id} no tiene conversión a USD (INTEG-04): no se puede aprobar porque se "
            "desconoce cuánto comprometería de la tesorería. Solo se puede rechazar."
        )


class TreasuryNotInitializedError(ConflictError):
    """Sin fila de tesorería no hay presupuesto que editar: crearla inventaría un saldo y una foto (F7.1, D2)."""

    def __init__(self, company_id: str):
        super().__init__(
            f"La empresa {company_id} aún no tiene saldo registrado: envía primero balance_usd para tomar la foto "
            "del saldo y luego edita el presupuesto."
        )


class PaymentCapExceededError(ConflictError):
    """FIN-04: el tope duro por pago no admite excepción humana; la factura solo se puede rechazar."""

    def __init__(self, invoice_id: int, message: str):
        super().__init__(f"La factura {invoice_id} no se puede aprobar: {message} Solo se puede rechazar.")


class InvalidDecisionStateError(ConflictError):
    def __init__(self, invoice_id: int, status: str):
        super().__init__(
            f"La factura {invoice_id} está en estado {status}; solo se pueden decidir facturas en SCALED_TO_HUMAN."
        )
