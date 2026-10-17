"""Handlers de main.py por tipo de error de dominio: NotFoundError → 404 y ConflictError → 409."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.domain.errors import InvalidDecisionStateError, InvoiceNotFoundError, UnconvertedAmountApprovalError
from app.main import app


class RaisingDecide:
    def __init__(self, error):
        self.error = error

    async def execute(self, *_args, **_kwargs):
        raise self.error


@pytest.mark.parametrize("error, status", [
    (InvoiceNotFoundError(7), 404),
    (InvalidDecisionStateError(7, "AUTO_APPROVED"), 409),
    (UnconvertedAmountApprovalError(7), 409),
])
def test_errores_de_dominio_se_responden_por_su_base(monkeypatch, error, status):
    # Sin "with": TestClient no corre el lifespan, así que no hace falta base de datos
    monkeypatch.setattr(app.state, "container", SimpleNamespace(decide_invoice=RaisingDecide(error)))

    response = TestClient(app).post("/api/invoices/7/decision", json={"decision": "APPROVE", "decided_by": "CFO Demo"})

    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


@pytest.mark.parametrize("decided_by", ["", "x" * 101])
def test_decision_sin_autor_valido_es_422_antes_del_caso_de_uso(monkeypatch, decided_by):
    monkeypatch.setattr(app.state, "container", SimpleNamespace(decide_invoice=RaisingDecide(AssertionError())))
    response = TestClient(app).post("/api/invoices/7/decision", json={"decision": "APPROVE", "decided_by": decided_by})
    assert response.status_code == 422
