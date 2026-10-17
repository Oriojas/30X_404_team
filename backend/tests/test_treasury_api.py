"""GET y PATCH /api/treasury: saldo de la foto, comprometido, disponible, presupuesto y gasto del mes.
Las sumas (ventana del mes, fecha de aprobación y foto en UTC) las cubre test_postgres_integration.py contra SQL real."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.adapters.inbound.api.routers import treasury
from app.core.domain.errors import ConflictError
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


def test_patch_con_presupuesto_no_mueve_la_foto():
    # Si el presupuesto moviera la foto, lo comprometido se liberaría sin que cambie el saldo (F7.1, D2)
    snapshot = datetime(2026, 10, 17, 14, 0)
    repo = FixedTreasury(committed_usd=1900.0, snapshot_at=snapshot)

    response = make_client(repo).patch("/api/treasury", json={"monthly_budget_usd": 12000})

    assert response.status_code == 200
    body = response.json()
    assert body["monthly_budget_usd"] == 12000
    assert body["balance_usd"] == 8500 and body["committed_usd"] == 1900 and body["snapshot_at"] == "2026-10-17T14:00:00Z"


def test_patch_con_saldo_y_presupuesto_cambia_ambos_y_toma_la_foto():
    repo = FixedTreasury(committed_usd=1900.0, snapshot_at=datetime(2026, 10, 17, 14, 0))

    response = make_client(repo).patch("/api/treasury", json={"balance_usd": 9000, "monthly_budget_usd": 12000})

    assert response.status_code == 200
    body = response.json()
    assert body["balance_usd"] == 9000 and body["monthly_budget_usd"] == 12000 and body["committed_usd"] == 0
    assert body["snapshot_at"] != "2026-10-17T14:00:00Z"


def test_patch_con_saldo_conserva_el_presupuesto_guardado():
    repo = FixedTreasury(monthly_budget_usd=12000)

    response = make_client(repo).patch("/api/treasury", json={"balance_usd": 9000})

    assert response.json()["monthly_budget_usd"] == 12000


def test_patch_presupuesto_sin_saldo_registrado_responde_409_y_no_crea_la_fila():
    repo = FixedTreasury(initialized=False)
    app = FastAPI()
    app.include_router(treasury.router)
    app.add_exception_handler(ConflictError, lambda _r, exc: JSONResponse(status_code=409, content={"detail": str(exc)}))
    app.state.container = SimpleNamespace(update_treasury=UpdateTreasuryBalanceUseCase(repo, "TEST"))

    response = TestClient(app).patch("/api/treasury", json={"monthly_budget_usd": 12000})

    assert response.status_code == 409
    assert "balance_usd" in response.json()["detail"]
    assert repo.initialized is False and repo.monthly_budget_usd == 25000


@pytest.mark.parametrize("payload", [
    {"balance_usd": 0}, {"balance_usd": -10}, {"balance_usd": "mucho"}, {},
    {"monthly_budget_usd": 0}, {"monthly_budget_usd": -1}, {"monthly_budget_usd": "mucho"},
    {"balance_usd": 9000, "monthly_budget_usd": 0},
])
def test_patch_rechaza_saldo_o_presupuesto_invalido(payload):
    repo = FixedTreasury(committed_usd=1900.0)

    response = make_client(repo).patch("/api/treasury", json=payload)

    assert response.status_code == 422
    assert repo.committed_usd == 1900.0 and repo.balance_usd == 8500 and repo.monthly_budget_usd == 25000


def test_el_caso_de_uso_rechaza_actualizar_sin_saldo_ni_presupuesto():
    # El "al menos uno" no vive solo en el esquema de la API: el Core no deja el presupuesto en NULL
    import asyncio
    from app.core.domain.errors import InvalidFieldError
    repo = FixedTreasury()
    with pytest.raises(InvalidFieldError):
        asyncio.run(UpdateTreasuryBalanceUseCase(repo, "TEST").execute())
    assert repo.monthly_budget_usd == 25000
