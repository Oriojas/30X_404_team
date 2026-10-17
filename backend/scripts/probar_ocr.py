"""
Prueba manual del OCR con la API real de Gemini, sin base de datos ni servidor.
Lee GEMINI_API_KEY y GEMINI_MODEL del `.env` de la raíz.

Uso (desde backend/):
    python -m scripts.probar_ocr                         # las facturas de tests/fixtures
    python -m scripts.probar_ocr ruta/a/factura.jpg      # cualquier JPG, PNG, WEBP o PDF
"""

import asyncio
import logging
import mimetypes
import sys
from dataclasses import asdict
from pathlib import Path

from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter
from app.config import get_settings

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


async def main(paths: list[Path]) -> None:
    settings = get_settings()
    if not settings.gemini_api_key:
        sys.exit("Falta GEMINI_API_KEY en el .env de la raíz.")
    adapter = GeminiOCRAdapter(settings.gemini_api_key, settings.gemini_model)
    print(f"Modelo: {settings.gemini_model}\n")
    for path in paths:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        invoice = await adapter.extract_invoice_data(path.read_bytes(), mime_type)
        print(f"== {path.name} ({mime_type})")
        for field, value in asdict(invoice).items():
            print(f"   {field:22} {value}")
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    args = [Path(arg) for arg in sys.argv[1:]]
    asyncio.run(main(args or sorted(p for p in FIXTURES.iterdir() if p.suffix in {".png", ".pdf"})))
