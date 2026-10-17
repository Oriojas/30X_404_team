# Validación — Fase 1: OCR real con Gemini

> La rama `feat/ocr-gemini` se puede mergear cuando se cumplen **todos** los criterios bloqueantes.

## Criterios bloqueantes

> Verificado el 17-oct-2026 en `feat/ocr-gemini`: 44 pasadas sin `GEMINI_API_KEY` y con la red bloqueada por proxy; 46 de 46 con `TEST_DATABASE_URL` (PostgreSQL 16 en Docker).

### Pruebas automáticas (cliente simulado, sin red)

- [x] `pytest` en `backend/` pasa completo, incluido `tests/test_architecture.py`.
- [x] `tests/test_gemini_ocr.py` cubre los casos del grupo 6.2 del plan:
  - Respuesta válida → todos los campos de `ExtractedInvoice` poblados.
  - `amount: 1500000.0` + `currency: "COP"` del modelo → se conservan tal cual.
  - `currency: null` (moneda ambigua) → `original_currency="XXX"` (la tubería escala por INTEG-04).
  - Tipos inesperados (monto `"abc"`, fecha `"15/11/2026"`) → `original_amount=0.0` y `due_date=None`, sin excepción.
  - Confianza fuera de rango o ausente → acotada a [0, 1] o `0.0`.
  - JSON inválido → extracción vacía, confianza `0.0`.
  - Sin API key → extracción vacía y cero llamadas al cliente.
  - Excepción del SDK → extracción vacía, confianza `0.0`, sin propagar la excepción.
  - `NaN`/`Infinity` en monto o confianza → `0.0`.
  - Llamada que supera `OCR_TIMEOUT_SECONDS` → extracción vacía.
  - Bytes y `mime_type` de los tres fixtures (dos imágenes y un PDF) llegan al cliente.
- [x] `tests/test_ocr_to_decision.py`: la subida por `POST /api/invoices/upload` termina en `REJECTED` (COMP-01) para el proveedor OFAC, en `SCALED_TO_HUMAN` por INTEG-04 con moneda ambigua y por INTEG-03 con confianza `NaN`.
- [x] El prompt enviado incluye las instrucciones de inferencia de moneda y de formato latino (verificado en la prueba con el cliente simulado).
- [x] Ninguna prueba requiere `GEMINI_API_KEY` ni acceso a internet.

### Fixtures

- [x] `backend/tests/fixtures/` contiene una factura ficticia en imagen y otra en PDF, con datos inventados (sin datos reales de personas o empresas) y un `README.md` con los valores esperados.
- [x] Los fixtures pesan menos de 10 MB y usan tipos aceptados por la subida (JPG/PNG/WEBP/PDF).

### Código y arquitectura

- [x] `backend/requirements.txt` ya no tiene `google-generativeai` y sí `google-genai`.
- [x] `GEMINI_MODEL` por defecto es `gemini-3.8-flash` en `app/config.py` y `.env.example`.
- [x] La llamada usa `client.aio.models.generate_content` (sin bloquear el event loop) con `response_json_schema` que pide `amount` numérico, `currency` ISO y `due_date` ISO.
- [x] El adaptador no contiene parseo de formatos ni reglas de negocio: no calcula completitud, no valida el código de moneda ni el signo del monto (eso lo hacen INTEG-03 e INTEG-04).
- [x] Las pruebas existentes de INTEG-03 e INTEG-04 siguen verdes sin modificaciones.
- [x] El Core (`app/core/**`) no importa `google.genai`; ningún módulo fuera de `app/config.py` usa `os.getenv`.
- [x] Los logs de falla no incluyen la API key ni el contenido del archivo.

### Documentación

- [x] `backend/README.md` ya no dice que el adaptador es un stub.
- [x] `specs/tech-stack.md` y `specs/roadmap.md` reflejan el estado final (OCR en uso, F1.x marcadas).

## Verificación recomendada (no bloquea el merge)

- [x] Con una key real, subir los fixtures por `POST /api/invoices/upload` y confirmar que la factura conocida produce la decisión esperada sin carga manual (criterio "Listo cuando" del roadmap). *Hecho con PostgreSQL + seed: `AUTO_APPROVED`, `SCALED_TO_HUMAN` (HITL-01) y `REJECTED` (COMP-01).*
- [x] Confirmar que el fixture con `$` sin código y NIT colombiano sale como `COP` (inferencia de moneda). *Las dos facturas colombianas salieron `COP`.*
- [x] Subir una imagen borrosa o que no sea factura y confirmar que escala por INTEG-03. *Gemini real devolvió todos los campos en `null` y confianza 0 en ambas → INTEG-03 (y INTEG-04 por moneda `XXX`).*

## Cómo correr

```bash
cd backend && pytest -q
```
