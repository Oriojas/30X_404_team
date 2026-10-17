"""GET /api/treasury: saldo y presupuesto de la cuenta Blinka más el gasto aprobado del mes."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import treasury
from app.core.use_cases import GetTreasuryUseCase

from .fakes import FixedTreasury, InMemoryInvoices


def test_treasury_devuelve_saldo_presupuesto_y_gasto_del_mes():
    invoices = InMemoryInvoices()
    invoices.items = {1: SimpleNamespace(usd_amount=450.0, decision_status="AUTO_APPROVED"),
                      2: SimpleNamespace(usd_amount=900.0, decision_status="REJECTED")}
    app = FastAPI()
    app.include_router(treasury.router)
    app.state.container = SimpleNamespace(get_treasury=GetTreasuryUseCase(FixedTreasury(), invoices, "TEST"))

    response = TestClient(app).get("/api/treasury")

    assert response.status_code == 200
    assert response.json() == {"balance_usd": 8500, "monthly_budget_usd": 25000, "month_spent_usd": 450.0}
