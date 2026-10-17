# Requisitos — Fase 1: OCR real con Gemini

> Rama: `feat/ocr-gemini` · Fase 1 de [roadmap.md](../roadmap.md) (F1.1 a F1.7).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

Hoy `GeminiOCRAdapter` (`backend/app/adapters/outbound/ocr/gemini_ocr.py`) es un stub: devuelve una extracción vacía con confianza 0, así que toda factura subida por archivo o por Telegram escala por `INTEG-03`. La tubería de 4 capas, la API y el webhook ya funcionan; solo falta la lectura real del documento.

Según la misión, **la IA solo extrae datos**: la decisión sigue siendo determinista en `rules_pipeline.py`. Ante cualquier duda, la factura escala; nunca se aprueba por defecto.

## Alcance

**Entra:**
- Migrar de `google-generativeai` (deprecado) a `google-genai` en `backend/requirements.txt`.
- Fijar `GEMINI_MODEL` por defecto en `gemini-3.8-flash` en `app/config.py` y `.env.example`.
- Implementar `GeminiOCRAdapter.extract_invoice_data(file_bytes, mime_type)` para JPG, PNG, WEBP y PDF.
- Esquema JSON de extracción y prompt en español.
- Normalización hecha por el modelo vía prompt y esquema (moneda ISO inferida, monto numérico, fecha ISO); el adaptador solo convierte tipos y deja las validaciones de negocio a la tubería (D3).
- Fallas seguras: nunca lanzar excepción hacia el caso de uso.
- Pruebas unitarias con cliente simulado y fixtures de facturas ficticias en el repo.
- Quitar del `backend/README.md` la nota de "stub" (línea ~173) y documentar la variable `GEMINI_MODEL`.

**No entra:**
- Cambios en la tubería de reglas, en `MIN_OCR_CONFIDENCE` (0.85) ni en el dominio, salvo lo estrictamente necesario.
- Ingesta idempotente y hash de archivos (Fase 2).
- Cambios en el frontend (Fase 3).
- Reintentos automáticos, cola de trabajos o caché de respuestas del modelo.
- Prueba contra la API real de Gemini dentro de `pytest`.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **SDK `google-genai`**, cliente asíncrono `client.aio.models.generate_content`. Sin `asyncio.to_thread`. | Ya decidido en tech-stack; el cliente async evita hilos y no bloquea el event loop. |
| D2 | **Modelo por defecto `gemini-3.8-flash`**, configurable con `GEMINI_MODEL`. | Es el Flash estable (GA) más reciente según la lista oficial de modelos de Google consultada el 17-oct-2026. La familia 2.5 tiene acceso limitado para proyectos nuevos y 1.5/2.0 están retiradas. |
| D3 | **La tubería ya valida; el adaptador no duplica.** `ocr_confidence_score` es la confianza que reporta el modelo, acotada a [0, 1]. No se calcula completitud en el adaptador porque `rules_pipeline._integrity` ya escala por INTEG-03 cuando falta `invoice_number` o `vendor_name`, cuando `original_amount <= 0` o cuando la confianza es menor que 0.85, y lista los campos faltantes en el Audit Log. La moneda no soportada ya escala por INTEG-04 y NIT/cuenta ya se comparan normalizados en la capa 1. | Se cumple la intención de la confianza mixta (un campo crítico faltante siempre escala) sin repetir reglas del Core en un adaptador, y el Audit Log explica el motivo exacto. |
| D4 | **Salida estructurada** con `response_mime_type="application/json"` y `response_schema`. Aun así se valida el JSON en el adaptador. | Reduce JSON inválido, pero el adaptador no confía ciegamente en él. |
| D5 | **El modelo normaliza; el adaptador valida.** El prompt y el `response_schema` piden los datos ya limpios: `amount` como número con punto decimal (interpretando el formato latino `1.500.000,00` → `1500000.00`), `currency` como código ISO 4217 y `due_date` como `AAAA-MM-DD`. El adaptador no parsea formatos ni aplica reglas: solo convierte tipos (monto a `float`, o `0.0` si no es numérico; fecha con `date.fromisoformat`, o `None`; textos vacíos a `None`). | Menos código propio; el modelo tiene el contexto del documento y la tubería ya rechaza o escala los valores inválidos (D3). |
| D6 | **Fallas seguras:** sin API key, error de red/timeout, respuesta bloqueada, JSON inválido o campos imposibles → `ExtractedInvoice` vacía (`original_amount=0.0`, `original_currency="USD"`, `ocr_confidence_score=0.0`). Se registra un `logging.warning` sin incluir el contenido del archivo ni la key. | Principio de tolerancia cero: la factura escala por INTEG-03 en lugar de romper el flujo. |
| D7 | **El modelo infiere la moneda** con la evidencia del documento: código o símbolo explícito (`COP`, `US$`, `R$`, `€`), país o ciudad del proveedor, tipo de identificación fiscal (NIT → COP, RFC → MXN, CNPJ/CPF → BRL, CUIT → ARS, EIN → USD) y palabras como "pesos colombianos". Devuelve el código ISO real aunque no esté en las tasas fijas (la tubería ya trata la moneda no soportada). Si la evidencia no alcanza (p. ej. `$` solo sin país), devuelve `null` y el adaptador usa `"XXX"` (código ISO 4217 para "sin moneda"). Como `XXX` no tiene tasa, la tubería escala por INTEG-04 sin cambios en el Core. El adaptador no valida el formato del código: cualquier valor sin tasa también cae en INTEG-04. | No asumir USD silenciosamente para una factura en COP; ante la duda, escalar con la regla que ya existe. |
| D8 | El cliente de `google-genai` se **inyecta** en el adaptador (parámetro opcional del constructor) para poder simularlo en pruebas; si no se pasa y hay key, se crea uno. | Pruebas sin red y sin dependencia de la key. |

## Esquema de extracción (respuesta del modelo)

| Campo | Tipo | Notas |
| :--- | :--- | :--- |
| `invoice_number` | string \| null | Número o consecutivo de la factura / cuenta de cobro. |
| `vendor_name` | string \| null | Razón social o nombre del proveedor. |
| `vendor_tax_id` | string \| null | NIT, RUT, RFC, CUIT, etc., sin espacios extra. |
| `bank_account` | string \| null | Cuenta destino tal como aparece. |
| `amount` | number \| null | Total a pagar, ya normalizado (punto decimal, sin separador de miles). |
| `currency` | string \| null | Código ISO 4217 en mayúsculas, inferido según D7; `null` si es ambiguo. |
| `due_date` | string \| null | Fecha de vencimiento en `AAAA-MM-DD`. |
| `confidence` | number | 0–1, autoevaluación del modelo sobre la legibilidad. |

El prompt incluye ejemplos explícitos del formato latino (`1.500.000,00` → `1500000.00`, `2.350,50` → `2350.50`) y de inferencia de moneda (NIT colombiano + `$` → `COP`) para reducir errores de separadores. Monedas con tasa fija hoy: USD, COP, MXN, EUR, BRL, ARS (`adapters/outbound/fx/static_rates.py`).

## Restricciones de arquitectura

- Todo el código nuevo vive en `app/adapters/outbound/ocr/`. El Core no importa `google.genai`.
- Imports absolutos desde `app`. Solo `app/config.py` lee variables de entorno.
- `tests/test_architecture.py` debe seguir verde.
- El prompt y el esquema viven junto al adaptador (`ocr/prompt.py` o constantes en `gemini_ocr.py`).
