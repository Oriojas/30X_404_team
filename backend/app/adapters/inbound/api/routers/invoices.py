"""Endpoints REST de facturas y Audit Log para el Dashboard de React."""

from typing import List

from fastapi import APIRouter, Depends

from .....container import Container
from ..dependencies import get_container
from ..schemas import InvoiceCreateRequest, InvoiceResponse

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(limit: int = 50, container: Container = Depends(get_container)):
    """Lista las facturas procesadas para el Dashboard de React."""
    invoices = await container.list_invoices.execute(limit)
    return [InvoiceResponse.from_domain(inv) for inv in invoices]


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(payload: InvoiceCreateRequest, container: Container = Depends(get_container)):
    """Evalúa una factura cargada manualmente contra la tubería de 4 capas."""
    processed = await container.process_invoice.from_extracted(
        payload.to_domain(), channel_source=payload.channel_source
    )
    return InvoiceResponse.from_domain(processed)
