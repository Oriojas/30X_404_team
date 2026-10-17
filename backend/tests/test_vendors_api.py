"""GET/POST/PATCH /api/vendors: lista permitida de beneficiarios (F7.3).
Pasa por la app de main.py para probar también los 404/409 de los handlers por tipo de error."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.domain.models import Vendor
from app.core.use_cases import CreateVendorUseCase, ListVendorsUseCase, UpdateVendorUseCase
from app.main import app

from .fakes import InMemoryVendors

AWS = Vendor("US-91-1646860", "Amazon Web Services LATAM", "US-CHASE-000123456", contract_amount_usd=1000)
PEP = Vendor("900.777.321-9", "Consultora Riesgo Político S.A.S.", "CO-BOGOTA-99988877766", is_pep=True,
             contract_amount_usd=2000)
NEW = {"tax_id": "901.555.010-2", "legal_name": "Diseño Creativo Bogotá S.A.S.",
       "bank_account": "CO-BANCOLOMBIA-55500011122", "contract_amount_usd": 900, "updated_by": "CFO Demo"}


@pytest.fixture()
def vendors(monkeypatch):
    repo = InMemoryVendors(AWS, PEP)
    monkeypatch.setattr(app.state, "container", SimpleNamespace(
        list_vendors=ListVendorsUseCase(repo), create_vendor=CreateVendorUseCase(repo),
        update_vendor=UpdateVendorUseCase(repo)))
    return repo


@pytest.fixture()
def client(vendors):
    return TestClient(app)


def test_lista_activos_e_inactivos_con_su_estado(client, vendors):
    vendors.vendors[0].active = False

    body = client.get("/api/vendors").json()

    assert [v["legal_name"] for v in body] == ["Amazon Web Services LATAM", "Consultora Riesgo Político S.A.S."]
    assert body[0]["active"] is False and body[1]["is_pep"] is True and body[0]["contract_amount_usd"] == 1000


def test_alta_queda_activa_sin_pep_y_con_autor_y_fecha_utc(client, vendors):
    response = client.post("/api/vendors", json={**NEW, "tax_id": "  901.555.010-2  "})

    assert response.status_code == 201
    body = response.json()
    assert body["tax_id"] == "901.555.010-2" and body["active"] is True and body["is_pep"] is False
    assert body["updated_by"] == "CFO Demo" and body["updated_at"].endswith("Z")
    saved_at = datetime.fromisoformat(body["updated_at"].replace("Z", ""))
    assert abs(saved_at - datetime.utcnow()) < timedelta(minutes=1)
    assert len(vendors.vendors) == 3


@pytest.mark.parametrize("change", [{"tax_id": AWS.tax_id}, {"legal_name": "AMAZON web services latam"}])
def test_alta_con_nit_o_razon_social_repetidos_responde_409(client, vendors, change):
    response = client.post("/api/vendors", json={**NEW, **change})

    assert response.status_code == 409
    assert "Ya existe un beneficiario" in response.json()["detail"]
    assert len(vendors.vendors) == 2


@pytest.mark.parametrize("change", [
    {"tax_id": ""}, {"legal_name": "   "}, {"bank_account": ""}, {"updated_by": ""},
    {"updated_by": "x" * 101}, {"tax_id": "x" * 51}, {"legal_name": "x" * 151}, {"bank_account": "x" * 81},
    {"contract_amount_usd": 0}, {"contract_amount_usd": -5}, {"is_pep": True}, {"active": False},
])
def test_alta_invalida_responde_422(client, vendors, change):
    assert client.post("/api/vendors", json={**NEW, **change}).status_code == 422
    assert len(vendors.vendors) == 2


def test_alta_sin_tarifa_es_valida(client):
    payload = {k: v for k, v in NEW.items() if k != "contract_amount_usd"}
    assert client.post("/api/vendors", json=payload).json()["contract_amount_usd"] is None


def test_edicion_cambia_campos_editables_y_registra_el_autor(client, vendors):
    response = client.patch("/api/vendors/1", json={"bank_account": "US-CHASE-999", "contract_amount_usd": 1500,
                                                     "updated_by": "Tesorería"})

    assert response.status_code == 200
    body = response.json()
    assert body["bank_account"] == "US-CHASE-999" and body["contract_amount_usd"] == 1500
    assert body["legal_name"] == AWS.legal_name and body["updated_by"] == "Tesorería"


def test_baja_logica_y_reactivacion(client, vendors):
    assert client.patch("/api/vendors/1", json={"active": False, "updated_by": "CFO Demo"}).json()["active"] is False
    assert vendors.vendors[0].active is False and len(vendors.vendors) == 2
    assert client.patch("/api/vendors/1", json={"active": True, "updated_by": "CFO Demo"}).json()["active"] is True


def test_tarifa_null_quita_la_tarifa_acordada(client):
    body = client.patch("/api/vendors/1", json={"contract_amount_usd": None, "updated_by": "CFO Demo"}).json()
    assert body["contract_amount_usd"] is None


@pytest.mark.parametrize("payload", [
    {"tax_id": "OTRO", "updated_by": "CFO Demo"}, {"is_pep": False, "updated_by": "CFO Demo"},
    {"legal_name": None, "updated_by": "CFO Demo"}, {"bank_account": None, "updated_by": "CFO Demo"},
    {"active": None, "updated_by": "CFO Demo"}, {"active": False}, {"legal_name": "", "updated_by": "CFO Demo"},
])
def test_edicion_invalida_o_de_campos_no_editables_responde_422(client, vendors, payload):
    assert client.patch("/api/vendors/2", json=payload).status_code == 422
    assert vendors.vendors[1].is_pep is True and vendors.vendors[1].tax_id == PEP.tax_id


def test_editar_a_una_razon_social_de_otro_responde_409(client, vendors):
    response = client.patch("/api/vendors/2", json={"legal_name": "amazon web services latam", "updated_by": "CFO"})
    assert response.status_code == 409
    assert vendors.vendors[1].legal_name == PEP.legal_name


def test_editar_conservando_su_propia_razon_social_es_valido(client):
    response = client.patch("/api/vendors/1", json={"legal_name": AWS.legal_name.upper(), "updated_by": "CFO"})
    assert response.status_code == 200


def test_editar_un_id_inexistente_responde_404(client):
    response = client.patch("/api/vendors/999", json={"active": False, "updated_by": "CFO Demo"})
    assert response.status_code == 404 and "999" in response.json()["detail"]


@pytest.mark.parametrize("change", [
    {"tax_id": "US911646860"}, {"tax_id": " us-91-1646860 "},          # mismo NIT con otro formato
    {"legal_name": "Amazon Web Services LATAM."}, {"legal_name": "AMAZON WEB-SERVICES latam"},
    {"legal_name": "Consultora Riesgo Politico SAS"},                    # sin tilde ni puntos
])
def test_alta_con_el_mismo_nit_o_nombre_en_otro_formato_responde_409(client, vendors, change):
    assert client.post("/api/vendors", json={**NEW, **change}).status_code == 409
    assert len(vendors.vendors) == 2
