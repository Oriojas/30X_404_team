"""
Adaptador de Salida: OCR & Visión Multimodal con Google Gemini (SDK google-genai)
Implementa OCRPort. Extrae datos estructurados desde fotos y documentos PDF de facturas.

El modelo entrega los datos ya normalizados (monto numérico, moneda ISO, fecha ISO). Este adaptador
solo convierte tipos: las validaciones de negocio (campos faltantes, monto <= 0, confianza baja,
moneda sin tasa) las aplica la tubería con INTEG-03 e INTEG-04.
"""

import asyncio
import json
import logging
import math
from datetime import date
from typing import Any, Optional

from google import genai
from google.genai import types

from app.core.domain.models import ExtractedInvoice

logger = logging.getLogger(__name__)

# ISO 4217 "sin moneda": no tiene tasa, así que la tubería escala por INTEG-04
UNKNOWN_CURRENCY = "XXX"
# Tope de espera de la llamada a Gemini: si se vence, la factura escala en vez de colgar el canal
OCR_TIMEOUT_SECONDS = 30

EXTRACTION_PROMPT = """Eres un extractor de datos de facturas y cuentas de cobro de proveedores en Latinoamérica.
Lee el documento adjunto y responde solo con el JSON del esquema. Reglas:

1. Extrae el TOTAL A PAGAR de la factura (no subtotales ni impuestos sueltos).
2. Si un dato no se ve o no es legible, devuelve null. Nunca inventes datos.
3. "amount": número con punto decimal y sin separador de miles. El formato latino usa punto para
   miles y coma para decimales: "1.500.000,00" -> 1500000.00, "2.350,50" -> 2350.50, "1.500.000" -> 1500000.
   El formato anglosajón usa coma para miles: "1,500,000.00" -> 1500000.00.
4. "currency": código ISO 4217 en mayúsculas. Si no aparece explícito, infiérelo con la evidencia del documento:
   símbolo (US$ -> USD, R$ -> BRL, € -> EUR, COL$ -> COP), país o ciudad del proveedor, tipo de identificación
   fiscal (NIT -> COP, RFC -> MXN, CNPJ/CPF -> BRL, CUIT -> ARS, RUC de Perú -> PEN, EIN -> USD) o palabras como
   "pesos colombianos". Ejemplo: "$ 1.500.000" con NIT colombiano -> "COP". Si la evidencia no alcanza
   (por ejemplo "$" sin país identificable), devuelve null.
5. "due_date": fecha de vencimiento en formato AAAA-MM-DD ("15/11/2026" -> "2026-11-15").
6. "vendor_tax_id" y "bank_account": tal como aparecen en el documento, sin espacios extra al inicio o al final.
7. "confidence": número entre 0 y 1 con tu seguridad sobre la legibilidad y exactitud de los datos extraídos.
"""

_NULLABLE_STRING = {"type": ["string", "null"]}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": _NULLABLE_STRING,
        "vendor_name": _NULLABLE_STRING,
        "vendor_tax_id": _NULLABLE_STRING,
        "bank_account": _NULLABLE_STRING,
        "amount": {"type": ["number", "null"]},
        "currency": _NULLABLE_STRING,
        "due_date": _NULLABLE_STRING,
        "confidence": {"type": "number"},
    },
    "required": ["invoice_number", "vendor_name", "vendor_tax_id", "bank_account",
                 "amount", "currency", "due_date", "confidence"],
}


def _empty_extraction() -> ExtractedInvoice:
    return ExtractedInvoice(
        invoice_number=None,
        vendor_name=None,
        original_amount=0.0,
        original_currency="USD",
        ocr_confidence_score=0.0,
    )


def _is_number(value: Any) -> bool:
    # json.loads acepta NaN e Infinity: un NaN pasaría por alto las comparaciones de la tubería (INTEG-03)
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: Any) -> Optional[str]:
    if isinstance(value, str) or _is_number(value):
        return str(value).strip() or None
    return None


def _amount(value: Any) -> float:
    # Sin parseo de texto: "1.500" no se puede interpretar sin ambigüedad
    return float(value) if _is_number(value) else 0.0


def _due_date(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _confidence(value: Any) -> float:
    return min(max(float(value), 0.0), 1.0) if _is_number(value) else 0.0


def to_extracted_invoice(data: dict) -> ExtractedInvoice:
    """Mapea la respuesta del modelo a ExtractedInvoice convirtiendo tipos, sin reglas de negocio."""
    return ExtractedInvoice(
        invoice_number=_text(data.get("invoice_number")),
        vendor_name=_text(data.get("vendor_name")),
        original_amount=_amount(data.get("amount")),
        original_currency=_text(data.get("currency")) or UNKNOWN_CURRENCY,
        vendor_tax_id=_text(data.get("vendor_tax_id")),
        bank_account=_text(data.get("bank_account")),
        due_date=_due_date(data.get("due_date")),
        ocr_confidence_score=_confidence(data.get("confidence")),
    )


class GeminiOCRAdapter:
    """Motor de extracción multimodal usando un modelo Flash de Gemini."""

    def __init__(self, api_key: Optional[str], model_name: str = "gemini-3.8-flash", client: Any = None):
        self.model_name = model_name
        self.client = client or (genai.Client(api_key=api_key) if api_key else None)

    async def extract_invoice_data(self, file_bytes: bytes, mime_type: str) -> ExtractedInvoice:
        """Envía el archivo a Gemini y retorna la factura estructurada; ante cualquier falla, extracción vacía."""
        if self.client is None:
            logger.warning("GEMINI_API_KEY no configurada: se devuelve una extracción vacía")
            return _empty_extraction()
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime_type), EXTRACTION_PROMPT],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=EXTRACTION_SCHEMA,
                        temperature=0,
                    ),
                ),
                timeout=OCR_TIMEOUT_SECONDS,
            )
            data = json.loads(response.text)
            if not isinstance(data, dict):
                raise ValueError("la respuesta no es un objeto JSON")
            return to_extracted_invoice(data)
        except Exception as exc:  # falla segura: la factura escala por INTEG-03
            logger.warning("Falla en la extracción con Gemini (%s): %s", self.model_name, type(exc).__name__)
            return _empty_extraction()
