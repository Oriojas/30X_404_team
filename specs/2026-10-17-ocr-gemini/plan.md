# Plan — Fase 1: OCR real con Gemini

> Rama: `feat/ocr-gemini`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).
> Cada grupo se puede terminar, probar y commitear por separado.

## 1. Dependencias y configuración (F1.1)

1.1. En `backend/requirements.txt`, reemplazar `google-generativeai` por `google-genai` (versión mínima vigente).
1.2. En `backend/app/config.py`, cambiar el valor por defecto de `gemini_model` a `gemini-3.8-flash`.
1.3. Actualizar `.env.example` (`GEMINI_MODEL=gemini-3.8-flash`).
1.4. En `specs/tech-stack.md`, marcar el OCR como "En uso" con el modelo fijado y quitar el pendiente de limpieza de `google-generativeai`.
1.5. Instalar dependencias y correr `pytest` para confirmar que nada se rompe.

## 2. Prompt y esquema con normalización incluida (F1.2 + F1.4)

2.1. Definir el `response_schema` (tabla de requirements.md): `amount` numérico, `currency` código ISO 4217, `due_date` `AAAA-MM-DD`, resto texto o `null`, y `confidence` 0–1.
2.2. Escribir el prompt en español, que le pide al modelo:
   - Extraer el **total a pagar**, devolver `null` en lo que no se vea y no inventar datos.
   - Convertir el monto a número con punto decimal, con ejemplos del formato latino (`1.500.000,00` → `1500000.00`, `2.350,50` → `2350.50`).
   - **Inferir la moneda** con la evidencia del documento (símbolo/código, país o ciudad, tipo de identificación fiscal: NIT → COP, RFC → MXN, CNPJ → BRL, CUIT → ARS) y devolver `null` si es ambigua (p. ej. `$` sin país).
   - Devolver la fecha de vencimiento en ISO.
2.3. Dejar prompt y esquema como constantes junto al adaptador.

## 3. Mapeo de la salida a `ExtractedInvoice`

3.1. Conversión de tipos, sin reglas de negocio (D3): `amount` a `float`, o `0.0` si no es numérico; `currency` tal cual, o `"XXX"` si es `null` (D7); `due_date` con `date.fromisoformat`, o `None`; textos vacíos a `None`; `confidence` acotada a [0, 1], o `0.0` si falta.
3.2. No se calcula completitud ni se valida el código de moneda: INTEG-03 cubre campos faltantes, monto ≤ 0 y confianza baja; INTEG-04 cubre moneda sin tasa.

## 4. Adaptador Gemini (F1.3)

4.1. Constructor `GeminiOCRAdapter(api_key, model_name="gemini-3.8-flash", client=None)`; crea `genai.Client(api_key=...)` solo si hay key y no se inyectó cliente.
4.2. `extract_invoice_data`: construir `types.Part.from_bytes(data=file_bytes, mime_type=mime_type)` + prompt y llamar a `await client.aio.models.generate_content(model=..., contents=..., config=GenerateContentConfig(response_mime_type="application/json", response_schema=..., temperature=0))`.
4.3. Parsear `response.text` con `json.loads` y construir `ExtractedInvoice` con el mapeo del grupo 3.
4.4. Actualizar el docstring del módulo (quitar "Gemini 1.5 Flash" y el TODO).
4.5. Verificar que `container.py` sigue construyendo el adaptador sin cambios (o ajustar la firma si hace falta).

## 5. Fallas seguras (F1.5)

5.1. Sin API key → extracción vacía sin llamar al SDK.
5.2. Envolver la llamada y el parseo: excepciones del SDK, timeout, `response.text` vacío/bloqueado, JSON inválido o con tipos inesperados → extracción vacía con confianza 0 y `logging.warning` (sin contenido del archivo ni key).
5.3. Monto no numérico → `original_amount=0.0`; la tubería escala por INTEG-03 ("Campos faltantes: monto").

## 6. Fixtures y pruebas del adaptador (F1.6)

6.1. Crear `backend/tests/fixtures/` con una factura ficticia en imagen (PNG/JPG) y otra en PDF, con datos de un proveedor del seed: monto en formato latino y moneda solo deducible por el NIT/país (símbolo `$` sin código), para ejercitar la inferencia en la prueba manual. Agregar un `README.md` corto con los valores esperados de cada una.
6.2. `backend/tests/test_gemini_ocr.py` con un cliente simulado (`client.aio.models.generate_content` asíncrono falso):
   - Respuesta válida → `ExtractedInvoice` completa y confianza = la del modelo.
   - El modelo devuelve `amount: 1500000.0` y `currency: "COP"` → se conservan tal cual.
   - El modelo devuelve `currency: null` → `original_currency="XXX"`.
   - Tipos inesperados (monto `"abc"`, fecha `"15/11/2026"`) → `original_amount=0.0` y `due_date=None`, sin excepción.
   - Confianza fuera de rango (`1.7`, `-0.2`, ausente) → acotada a [0, 1] o `0.0`.
   - JSON inválido → extracción vacía, confianza 0.
   - Sin API key → extracción vacía y el cliente nunca se llama.
   - El SDK lanza excepción → extracción vacía, confianza 0.
   - Verificar que se envían los bytes y el `mime_type` del fixture (imagen y PDF).
6.3. No se agregan pruebas de tubería: INTEG-03 (campos faltantes, confianza baja) e INTEG-04 (moneda sin tasa) ya están cubiertas en `test_rules_pipeline.py` y `test_process_invoice.py`.
6.4. Correr toda la suite (`pytest`), incluida la prueba de arquitectura.

## 7. Documentación y prueba manual opcional (F1.7)

7.1. Quitar la nota de "stub" de `backend/README.md` y explicar `GEMINI_API_KEY` / `GEMINI_MODEL` y el comportamiento ante fallas.
7.2. (Opcional, no bloquea el merge) Subir los dos fixtures por `POST /api/invoices/upload` con una key real y anotar el resultado en el PR.
7.3. Marcar F1.1 a F1.7 como `[x]` en `specs/roadmap.md`.
