"""Endpoints REST de facturas y Audit Log para el Dashboard de React."""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.adapters.inbound.api.schemas import HumanDecisionRequest, InvoiceCreateRequest, InvoiceResponse
from app.adapters.inbound.dependencies import get_decide_invoice, get_list_invoices, get_process_invoice
from app.core.use_cases import DecideInvoiceUseCase, ListInvoicesUseCase, ProcessInvoiceUseCase

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(limit: int = 50, use_case: ListInvoicesUseCase = Depends(get_list_invoices)):
    """Lista las facturas procesadas para el Dashboard de React."""
    invoices = await use_case.execute(limit)
    return [InvoiceResponse.from_domain(inv) for inv in invoices]


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    payload: InvoiceCreateRequest, use_case: ProcessInvoiceUseCase = Depends(get_process_invoice)
):
    """Evalúa una factura con datos ya estructurados (sin OCR) contra la tubería de 4 capas."""
    processed = await use_case.from_extracted(
        payload.to_domain(), channel_source=payload.channel_source
    )
    return InvoiceResponse.from_domain(processed)


@router.post("/upload", response_model=InvoiceResponse, status_code=201)
async def upload_invoice(
    file: UploadFile = File(...), use_case: ProcessInvoiceUseCase = Depends(get_process_invoice)
):
    """Canal de ingesta web: recibe una foto o PDF, la pasa por OCR y la evalúa."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Tipo de archivo no soportado: {file.content_type}. Usa JPG, PNG, WEBP o PDF.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "El archivo supera el límite de 10 MB.")
    if not content:
        raise HTTPException(400, "El archivo está vacío.")

    processed = await use_case.from_document(content, file.content_type, channel_source="WEB")
    return InvoiceResponse.from_domain(processed)


@router.post("/{invoice_id}/decision", response_model=InvoiceResponse)
async def decide_invoice(
    invoice_id: int, payload: HumanDecisionRequest, use_case: DecideInvoiceUseCase = Depends(get_decide_invoice)
):
    """Aprobación o rechazo humano de una factura en SCALED_TO_HUMAN (solo desde el dashboard)."""
    updated = await use_case.execute(
        invoice_id, payload.decision, payload.decided_by, payload.note
    )
    return InvoiceResponse.from_domain(updated)
