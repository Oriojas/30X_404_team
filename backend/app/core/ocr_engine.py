"""
Módulo Core: OCR & Visión Multimodal con Google Gemini 1.5 Flash
Extrae datos estructurados desde fotos y documentos PDF de facturas.
"""

import os
from typing import Dict, Any, Optional


class GeminiOCREngine:
    """Motor de extracción multimodal usando Gemini 1.5 Flash."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    async def extract_invoice_data(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Envía el archivo a Gemini y retorna el JSON estructurado."""
        # TODO: Implementar llamada al SDK google-generativeai
        return {
            "invoice_number": None,
            "vendor_name": None,
            "vendor_tax_id": None,
            "original_amount": 0.0,
            "original_currency": "USD",
            "due_date": None,
            "ocr_confidence_score": 0.0
        }
