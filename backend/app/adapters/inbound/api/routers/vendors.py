"""Endpoints REST de la lista permitida de beneficiarios (F7.3).
404 y 409 salen de los handlers por tipo de error de main.py."""

from typing import List

from fastapi import APIRouter, Depends

from app.adapters.inbound.api.schemas import VendorCreate, VendorResponse, VendorUpdate
from app.adapters.inbound.dependencies import get_create_vendor, get_list_vendors, get_update_vendor
from app.core.use_cases import CreateVendorUseCase, ListVendorsUseCase, UpdateVendorUseCase

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("", response_model=List[VendorResponse])
async def list_vendors(use_case: ListVendorsUseCase = Depends(get_list_vendors)):
    """Beneficiarios activos e inactivos, con su cuenta autorizada, tarifa acordada y último cambio."""
    return [VendorResponse.from_domain(v) for v in await use_case.execute()]


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(payload: VendorCreate, use_case: CreateVendorUseCase = Depends(get_create_vendor)):
    """Alta en la lista permitida: sus facturas dejan de escalar por HITL-02. 409 si el NIT o la razón social existen."""
    vendor = await use_case.execute(payload.tax_id, payload.legal_name, payload.bank_account,
                                    payload.contract_amount_usd, payload.updated_by)
    return VendorResponse.from_domain(vendor)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(vendor_id: int, payload: VendorUpdate,
                        use_case: UpdateVendorUseCase = Depends(get_update_vendor)):
    """Edita razón social, cuenta, tarifa o estado (active = false es la baja lógica)."""
    return VendorResponse.from_domain(await use_case.execute(vendor_id, payload.changes(), payload.updated_by))
