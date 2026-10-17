"""
Pruebas del adaptador GeminiOCRAdapter con un cliente simulado: sin red ni GEMINI_API_KEY.
Las reglas de negocio (INTEG-03, INTEG-04) se prueban en la tubería; aquí solo el mapeo y las fallas seguras.
"""

import asyncio
import json
from datetime import date
from pathlib import Path

from app.adapters.outbound.ocr import gemini_ocr
from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter

from .fakes import FakeGenAIClient

FIXTURES = Path(__file__).parent / "fixtures"

VALID = {
    "invoice_number": "DS-2026-1107",
    "vendor_name": "DevStudio LatAm S.A.S.",
    "vendor_tax_id": "900.584.112-4",
    "bank_account": "CO-BANCOLOMBIA-11122233344",
    "amount": 4200000.0,
    "currency": "COP",
    "due_date": "2026-11-30",
    "confidence": 0.93,
}


def extract(client, file_bytes=b"img", mime_type="image/png", api_key="test-key"):
    adapter = GeminiOCRAdapter(api_key, "gemini-test", client=client)
    return asyncio.run(adapter.extract_invoice_data(file_bytes, mime_type))


def respond(**overrides):
    return FakeGenAIClient(text=json.dumps({**VALID, **overrides}))


def assert_empty(invoice):
    assert invoice.invoice_number is None and invoice.vendor_name is None
    assert invoice.original_amount == 0.0 and invoice.ocr_confidence_score == 0.0


def test_respuesta_valida_mapea_todos_los_campos():
    invoice = extract(respond())
    assert invoice.invoice_number == "DS-2026-1107"
    assert invoice.vendor_name == "DevStudio LatAm S.A.S."
    assert invoice.vendor_tax_id == "900.584.112-4"
    assert invoice.bank_account == "CO-BANCOLOMBIA-11122233344"
    assert invoice.original_amount == 4200000.0
    assert invoice.original_currency == "COP"
    assert invoice.due_date == date(2026, 11, 30)
    assert invoice.ocr_confidence_score == 0.93


def test_moneda_ambigua_queda_como_xxx():
    assert extract(respond(currency=None)).original_currency == "XXX"


def test_tipos_inesperados_no_se_parsean_ni_rompen():
    invoice = extract(respond(amount="1.500.000,00", due_date="15/11/2026", vendor_name="  "))
    assert invoice.original_amount == 0.0
    assert invoice.due_date is None
    assert invoice.vendor_name is None


def test_confianza_fuera_de_rango_se_acota():
    assert extract(respond(confidence=1.7)).ocr_confidence_score == 1.0
    assert extract(respond(confidence=-0.2)).ocr_confidence_score == 0.0
    assert extract(respond(confidence=None)).ocr_confidence_score == 0.0


def test_nan_e_infinito_no_pasan_como_numeros():
    # json.loads acepta NaN: si llegara a la tubería, "NaN < 0.85" es False y saltaría INTEG-03
    invoice = extract(FakeGenAIClient(text='{"amount": NaN, "confidence": NaN, "invoice_number": "A"}'))
    assert invoice.original_amount == 0.0 and invoice.ocr_confidence_score == 0.0
    assert extract(FakeGenAIClient(text='{"amount": Infinity, "confidence": 0.9}')).original_amount == 0.0


def test_json_invalido_devuelve_extraccion_vacia():
    assert_empty(extract(FakeGenAIClient(text="no es json")))
    assert_empty(extract(FakeGenAIClient(text="[1, 2]")))
    assert_empty(extract(FakeGenAIClient(text=None)))  # respuesta bloqueada


def test_sin_api_key_no_llama_al_cliente():
    adapter = GeminiOCRAdapter(None, "gemini-test")
    assert adapter.client is None
    assert_empty(asyncio.run(adapter.extract_invoice_data(b"img", "image/png")))


def test_excepcion_del_sdk_no_se_propaga():
    client = FakeGenAIClient(error=TimeoutError("timeout"))
    assert_empty(extract(client))
    assert len(client.calls) == 1


def test_llamada_lenta_se_corta_por_timeout(monkeypatch):
    monkeypatch.setattr(gemini_ocr, "OCR_TIMEOUT_SECONDS", 0.01)
    assert_empty(extract(FakeGenAIClient(text=json.dumps(VALID), delay=1)))


def test_envia_bytes_mime_prompt_y_esquema_de_los_fixtures():
    for name, mime_type in (("factura_devstudio.png", "image/png"), ("factura_nube_andina.pdf", "application/pdf"),
                            ("factura_global_trade.png", "image/png")):
        file_bytes = (FIXTURES / name).read_bytes()
        client = respond()
        extract(client, file_bytes, mime_type)

        call = client.calls[0]
        part, prompt = call["contents"]
        assert part.inline_data.data == file_bytes and part.inline_data.mime_type == mime_type
        assert call["model"] == "gemini-test"
        assert "1.500.000,00" in prompt and "NIT -> COP" in prompt
        assert call["config"].response_mime_type == "application/json"
        assert call["config"].response_json_schema["properties"]["amount"]["type"] == ["number", "null"]
