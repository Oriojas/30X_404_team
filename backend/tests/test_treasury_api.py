"""GET /api/treasury: saldo, presupuesto y gasto aprobado del mes de la cuenta Blinka.
La suma del mes (ventana y estados aprobados) la cubre test_postgres_integration.py contra SQL real."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import treasury
from app.core.use_cases import GetTreasuryUseCase

from .fakes import FixedTreasury


def test_treasury_devuelve_saldo_presupuesto_y_gasto_del_mes():
    app = FastAPI()
    app.include_router(treasury.router)
    app.state.container = SimpleNamespace(get_treasury=GetTreasuryUseCase(FixedTreasury(month_spent_usd=450.0), "TEST"))

    response = TestClient(app).get("/api/treasury")

    assert response.status_code == 200
    assert response.json() == {"balance_usd": 8500, "monthly_budget_usd": 25000, "month_spent_usd": 450.0}
