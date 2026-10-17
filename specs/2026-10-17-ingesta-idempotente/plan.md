# Plan — Fase 2: Ingesta idempotente en todos los canales

> Rama: `feat/ingesta-idempotente`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).
> Cada grupo se puede terminar, probar y commitear por separado.

## 1. Esquema (F2.1)

1.1. En `backend/app/adapters/outbound/db/schema.sql`, agregar la tabla `ingested_messages` con `PRIMARY KEY (channel, external_id)`, después de `invoices` (por la llave foránea).
1.2. Agregar `ALTER TABLE invoices ADD COLUMN IF NOT EXISTS file_sha256 CHAR(64)` y el índice `idx_invoices_file_sha256`.
1.3. Confirmar que `schema.sql` se puede ejecutar dos veces seguidas sin error (idempotente) y que `seed.sql` no cambia.

## 2. Dominio y puerto (F2.2)

2.1. En `core/domain/models.py`: `IngestionRecord(status, invoice_id)`, `IngestionResult(invoice, duplicate, in_progress)` y el campo opcional `file_sha256` en `ProcessedInvoice`.
2.2. En `core/ports/outbound.py`: `IngestionLog` con `claim`, `complete` y `release`; sumar `find_by_file_hash` a `InvoiceRepository`.
2.3. Fake en memoria `FakeIngestionLog` en `tests/fakes.py` (con un `asyncio.Lock` para simular la atomicidad) y `find_by_file_hash` en el repositorio falso.

## 3. Adaptador PostgreSQL (F2.2)

3.1. `PostgresIngestionLog` en `adapters/outbound/db/postgres_repository.py`:
   - `claim`: `INSERT ... ON CONFLICT (channel, external_id) DO UPDATE SET received_at = NOW() WHERE ingested_messages.status = 'PROCESSING' AND ingested_messages.received_at < NOW() - interval` con `RETURNING`. Si devuelve fila, ganó; si no, `SELECT` del registro existente (D1, D5).
   - `complete`: `UPDATE ... SET status = 'COMPLETED', invoice_id = $3`.
   - `release`: `DELETE` solo si sigue en `PROCESSING`.
3.2. `save` persiste `file_sha256`; `_row_to_invoice` lo lee.
3.3. `find_by_file_hash`: última factura con ese hash, estado en `NOT_REJECTED`, dentro de la ventana.
3.4. Cablear `PostgresIngestionLog` en `container.py` y pasarlo a `ProcessInvoiceUseCase`.

## 4. Caso de uso (F2.3 + F2.6)

4.1. `ProcessInvoiceUseCase.__init__` recibe `ingestion: Optional[IngestionLog] = None` (sin log, se comporta como hoy).
4.2. Envoltorio privado `_idempotent(channel, external_id, work)` que aplica D9: `claim` → si hay registro devolver `IngestionResult(duplicate=True, in_progress=status == "PROCESSING", invoice=...)` → ejecutar `work` → `complete` → `notify_decision`; ante cualquier excepción (incluida la cancelación) `release` y relanzar.
4.3. `from_document(..., external_id=None)` y `from_extracted(..., external_id=None)` devuelven `IngestionResult`; `notify_received` queda dentro del trabajo reclamado.
4.4. En `from_document`, calcular `hashlib.sha256(file_bytes).hexdigest()`. Si `find_by_file_hash` encuentra una factura dentro de `duplicate_check_days`, saltar el OCR, reconstruir el `ExtractedInvoice` con sus datos y evaluar con `is_duplicate=True` y una explicación INTEG-01 que cite la factura original (D8).
4.5. Guardar el hash en la factura nueva en todos los casos.
4.6. Ajustar `test_process_invoice.py` y `test_ocr_to_decision.py` al nuevo tipo de retorno.

## 5. Telegram (F2.4)

5.1. En `adapters/inbound/telegram/webhook.py`, leer `update["update_id"]` y pasarlo como `external_id` (`str`).
5.2. Respuesta: `{"status": "processed", "decision": ...}` la primera vez; `{"status": "duplicate"}` (con `decision` si ya hay factura) en las repeticiones, siempre `200`.
5.3. Evitar descargar el archivo de Telegram en una repetición: reclamar antes de `download_file` (el caso de uso expone el reclamo o el webhook recibe la descarga como callable perezoso; elegir lo más simple al implementar sin romper la arquitectura).
5.4. Pruebas en `test_telegram_webhook.py`: el mismo update dos veces → una factura, un aviso, segunda respuesta `duplicate`.

## 6. Web y API (F2.5)

6.1. En `adapters/inbound/api/routers/invoices.py`, leer `Idempotency-Key: Optional[str] = Header(None)` en `POST /api/invoices` (canal `API`) y `POST /api/invoices/upload` (canal `WEB`).
6.2. Traducir `IngestionResult`: nueva → `201`; repetida con factura → `200` y el mismo cuerpo; en proceso → `409` con el mensaje de D3. Usar `Response.status_code` en vez del `status_code` fijo del decorador.
6.3. Validar la clave: no vacía, máximo 200 caracteres (`422` si no cumple).
6.4. Pruebas de API: la misma clave dos veces (`201` y `200`, mismo `id`), sin header (dos facturas, como hoy), clave en proceso (`409`), la misma clave en `/upload` y en `/` no colisiona.

## 7. Pruebas de concurrencia, reintento y cruce de canales (F2.7)

7.1. Reintento tras fallo: el OCR simulado lanza excepción la primera vez → la segunda llamada con la misma clave sí procesa.
7.2. Concurrencia: dos `from_document` con la misma clave en `asyncio.gather` → exactamente una factura y un `notify_decision`.
7.3. Cruce de canales: el mismo archivo por Telegram y luego por web → la segunda queda `REJECTED` por INTEG-01, el OCR se llamó una sola vez y la explicación cita la factura original.
7.4. Hash fuera de la ventana o factura original rechazada → se procesa normalmente.
7.5. En `test_postgres_integration.py`: `claim` concurrente real (dos conexiones), `complete`/`release`, retoma de un reclamo vencido y `find_by_file_hash`.
7.6. Correr toda la suite (`pytest`), incluida la prueba de arquitectura.

## 8. Documentación y cierre

8.1. `backend/README.md`: header `Idempotency-Key`, respuestas `200`/`201`/`409` y respuesta `duplicate` del webhook.
8.2. `specs/roadmap.md`: marcar F2.1 a F2.7.
8.3. `specs/tech-stack.md`: quitar "(desde la Fase 2 del roadmap)" de la sección de ingesta idempotente.
8.4. Completar [validation.md](validation.md) y abrir el PR.
