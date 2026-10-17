"""Endpoints REST de facturas y Audit Log para el Dashboard de React.

Idempotencia: los POST de ingesta aceptan el header Idempotency-Key. Una clave repetida devuelve la misma
factura (200 en vez de 201); si la primera solicitud aún se procesa, 409 y el cliente reintenta con la misma clave.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile

from app.adapters.inbound.api.schemas import HumanDecisionRequest, InvoiceCreateRequest, InvoiceResponse
from app.adapters.inbound.dependencies import get_decide_invoice, get_list_invoices, get_process_invoice
from app.core.domain.models import IngestionResult
from app.core.use_cases import DecideInvoiceUseCase, ListInvoicesUseCase, ProcessInvoiceUseCase

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

IdempotencyKey = Header(default=None, alias="Idempotency-Key", min_length=1, max_length=200)


def ingestion_response(result: IngestionResult, response: Response) -> InvoiceResponse:
    """201 para una factura nueva, 200 para una repetida y 409 si la primera entrega sigue en proceso."""
    if result.in_progress:
        raise HTTPException(409, "La factura con esta Idempotency-Key aún se está procesando.")
    if result.duplicate:
        response.status_code = 200
    return InvoiceResponse.from_domain(result.invoice)


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(limit: int = 50, use_case: ListInvoicesUseCase = Depends(get_list_invoices)):
    """Lista las facturas procesadas para el Dashboard de React."""
    invoices = await use_case.execute(limit)
    return [InvoiceResponse.from_domain(inv) for inv in invoices]


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    payload: InvoiceCreateRequest,
    response: Response,
    idempotency_key: Optional[str] = IdempotencyKey,
    use_case: ProcessInvoiceUseCase = Depends(get_process_invoice),
):
    """Evalúa una factura con datos ya estructurados (sin OCR) contra la tubería de 4 capas."""
    result = await use_case.from_extracted(
        payload.to_domain(), channel_source=payload.channel_source,
        external_id=idempotency_key, ingestion_channel="API",
    )
    return ingestion_response(result, response)


@router.post("/upload", response_model=InvoiceResponse, status_code=201)
async def upload_invoice(
    response: Response,
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = IdempotencyKey,
    use_case: ProcessInvoiceUseCase = Depends(get_process_invoice),
):
    """Canal de ingesta web: recibe una foto o PDF, la pasa por OCR y la evalúa."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Tipo de archivo no soportado: {file.content_type}. Usa JPG, PNG, WEBP o PDF.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "El archivo supera el límite de 10 MB.")
    if not content:
        raise HTTPException(400, "El archivo está vacío.")

    result = await use_case.from_document(
        content, file.content_type, channel_source="WEB", external_id=idempotency_key
    )
    return ingestion_response(result, response)


@router.post("/{invoice_id}/decision", response_model=InvoiceResponse)
async def decide_invoice(
    invoice_id: int, payload: HumanDecisionRequest, use_case: DecideInvoiceUseCase = Depends(get_decide_invoice)
):
    """Aprobación o rechazo humano de una factura en SCALED_TO_HUMAN (solo desde el dashboard)."""
    updated = await use_case.execute(
        invoice_id, payload.decision, payload.decided_by, payload.note
    )
    return InvoiceResponse.from_domain(updated)
