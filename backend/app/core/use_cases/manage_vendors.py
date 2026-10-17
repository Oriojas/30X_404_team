"""Casos de Uso: lista permitida de beneficiarios (alta, edición y baja lógica) desde el Dashboard.
El alta por un aprobador es la verificación inicial del proveedor (HITL-02) y queda con quién y cuándo."""

from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.domain.errors import VendorNotFoundError
from app.core.domain.models import Vendor
from app.core.ports.outbound import VendorRepository

# tax_id es la llave con que COMP-04 compara la factura e is_pep lo define cumplimiento: no se editan
EDITABLE_FIELDS = ("legal_name", "bank_account", "contract_amount_usd", "active")


class ListVendorsUseCase:
    def __init__(self, vendors: VendorRepository):
        self.vendors = vendors

    async def execute(self) -> List[Vendor]:
        return await self.vendors.list_all()


class CreateVendorUseCase:
    def __init__(self, vendors: VendorRepository):
        self.vendors = vendors

    async def execute(self, tax_id: str, legal_name: str, bank_account: str,
                      contract_amount_usd: Optional[float], updated_by: str) -> Vendor:
        # updated_at con el reloj de la app en UTC, como processed_at y decided_at
        return await self.vendors.create(Vendor(
            tax_id=tax_id, legal_name=legal_name, bank_account=bank_account, is_pep=False,
            contract_amount_usd=contract_amount_usd, active=True, updated_by=updated_by,
            updated_at=datetime.utcnow(),
        ))


class UpdateVendorUseCase:
    def __init__(self, vendors: VendorRepository):
        self.vendors = vendors

    async def execute(self, vendor_id: int, changes: Dict[str, Any], updated_by: str) -> Vendor:
        """Aplica solo los campos editables enviados; contract_amount_usd = None quita la tarifa acordada."""
        current = await self.vendors.get(vendor_id)
        if current is None:
            raise VendorNotFoundError(vendor_id)
        updates = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS}
        return await self.vendors.update(
            replace(current, **updates, updated_by=updated_by, updated_at=datetime.utcnow()))
