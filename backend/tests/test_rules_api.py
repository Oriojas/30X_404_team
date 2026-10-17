"""POST /api/rules: el tope por pago (FIN-04) no puede quedar por debajo del umbral autónomo (F7.2, D4).
Pasa por la app de main.py para probar también la forma del 422 que lee el dashboard (ApiError.fieldErrors)."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.domain.errors import InvalidRulesError
from app.core.use_cases import GetRulesUseCase, UpdateRulesUseCase
from app.main import app

from .fakes import InMemoryRules


@pytest.fixture()
def rules(monkeypatch):
    repo = InMemoryRules()  # umbral $2,000 y tope $20,000 por defecto
    monkeypatch.setattr(app.state, "container", SimpleNamespace(get_rules=GetRulesUseCase(repo, "TEST"),
                                                                update_rules=UpdateRulesUseCase(repo, "TEST")))
    return repo


def test_get_y_post_exponen_el_tope_por_pago(rules):
    client = TestClient(app)
    assert client.get("/api/rules").json()["max_payment_usd"] == 20000

    response = client.post("/api/rules", json={"max_payment_usd": 15000})

    assert response.status_code == 200 and response.json()["max_payment_usd"] == 15000
    assert rules.current.max_payment_usd == 15000 and rules.current.max_autonomous_usd == 2000


@pytest.mark.parametrize("payload, field", [
    ({"max_payment_usd": 1500}, "max_payment_usd"),             # tope bajo el umbral guardado
    ({"max_autonomous_usd": 25000}, "max_autonomous_usd"),      # umbral sobre el tope guardado
    ({"max_autonomous_usd": 5000, "max_payment_usd": 4000}, "max_payment_usd"),
])
def test_tope_bajo_el_umbral_responde_422_con_el_campo_y_no_guarda(rules, payload, field):
    response = TestClient(app).post("/api/rules", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", field] and "tope por pago" in detail[0]["msg"]
    assert rules.current.max_payment_usd == 20000 and rules.current.max_autonomous_usd == 2000


def test_tope_igual_al_umbral_es_valido(rules):
    response = TestClient(app).post("/api/rules", json={"max_autonomous_usd": 5000, "max_payment_usd": 5000})
    assert response.status_code == 200


def test_tope_negativo_es_422_de_validacion(rules):
    assert TestClient(app).post("/api/rules", json={"max_payment_usd": -1}).status_code == 422


def test_el_caso_de_uso_valida_contra_lo_guardado():
    repo = InMemoryRules(max_payment_usd=3000)
    with pytest.raises(InvalidRulesError) as error:
        asyncio.run(UpdateRulesUseCase(repo, "TEST").execute({"max_autonomous_usd": 3500}))
    assert error.value.field == "max_autonomous_usd"
