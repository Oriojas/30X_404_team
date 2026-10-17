"""
Adaptador de Salida: OCR & Visión Multimodal con Google Gemini 1.5 Flash
Implementa OCRPort. Extrae datos estructurados desde fotos y documentos PDF de facturas.
"""

from typing import Optional

from ....core.domain.models import ExtractedInvoice


class GeminiOCRAdapter:
    """Motor de extracción multimodal usando Gemini 1.5 Flash."""

    def __init__(self, api_key: Optional[str], model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    async def extract_invoice_data(self, file_bytes: bytes, mime_type: str) -> ExtractedInvoice:
        """Envía el archivo a Gemini y retorna la factura estructurada."""
        # TODO: Implementar llamada al SDK google-generativeai
        return ExtractedInvoice(
            invoice_number=None,
            vendor_name=None,
            original_amount=0.0,
            original_currency="USD",
            ocr_confidence_score=0.0,
        )
