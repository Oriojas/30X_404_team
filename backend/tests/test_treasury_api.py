"""GET y PATCH /api/treasury: saldo de la foto, comprometido, disponible, presupuesto y gasto del mes.
Las sumas (ventana del mes, fecha de aprobación y foto en UTC) las cubre test_postgres_integration.py contra SQL real."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import treasury
from app.core.use_cases import GetTreasuryUseCase, UpdateTreasuryBalanceUseCase

from app.core.domain.models import DecisionStatus, ProcessedInvoice

from .fakes import FixedTreasury, InMemoryInvoices, LedgerTreasury


def make_client(repo):
    app = FastAPI()
    app.include_router(treasury.router)
    app.state.container = SimpleNamespace(get_treasury=GetTreasuryUseCase(repo, "TEST"),
                                          update_treasury=UpdateTreasuryBalanceUseCase(repo, "TEST"))
    return TestClient(app)


def test_treasury_devuelve_saldo_comprometido_disponible_y_gasto_del_mes():
    repo = FixedTreasury(month_spent_usd=450.0, committed_usd=1900.0, snapshot_at=datetime(2026, 10, 17, 14, 0))

    response = make_client(repo).get("/api/treasury")

    assert response.status_code == 200
    assert response.json() == {"balance_usd": 8500, "committed_usd": 1900.0, "available_usd": 6600.0,
                               "snapshot_at": "2026-10-17T14:00:00Z",
                               "monthly_budget_usd": 25000, "month_spent_usd": 450.0}


def test_patch_toma_una_foto_nueva_y_libera_lo_comprometido():
    # Aprobada después de la foto vieja: compromete hasta que el PATCH toma una foto con la hora actual
    invoices = InMemoryInvoices()
    invoices.items[1] = ProcessedInvoice(
        id=1, invoice_number="A", vendor_name="Proveedor", original_amount=1900, original_currency="USD",
        usd_amount=1900, fx_rate_applied=1.0, decision_status=DecisionStatus.AUTO_APPROVED, audit_explanation="x",
        processed_at=datetime.utcnow() - timedelta(minutes=5))
    client = make_client(LedgerTreasury(invoices, snapshot_at=datetime.utcnow() - timedelta(days=1)))
    assert client.get("/api/treasury").json()["committed_usd"] == 1900

    response = client.patch("/api/treasury", json={"balance_usd": 8500})

    assert response.status_code == 200
    body = response.json()
    assert body["balance_usd"] == 8500 and body["committed_usd"] == 0 and body["available_usd"] == 8500
    assert body["snapshot_at"].endswith("Z")


def test_patch_ignora_el_presupuesto_hasta_la_fase_7():
    repo = FixedTreasury()

    response = make_client(repo).patch("/api/treasury", json={"balance_usd": 9000, "monthly_budget_usd": 1})

    assert response.status_code == 200
    assert response.json()["balance_usd"] == 9000 and response.json()["monthly_budget_usd"] == 25000


@pytest.mark.parametrize("payload", [{"balance_usd": 0}, {"balance_usd": -10}, {"balance_usd": "mucho"}, {}])
def test_patch_rechaza_saldo_invalido(payload):
    repo = FixedTreasury(committed_usd=1900.0)

    response = make_client(repo).patch("/api/treasury", json=payload)

    assert response.status_code == 422
    assert repo.committed_usd == 1900.0
