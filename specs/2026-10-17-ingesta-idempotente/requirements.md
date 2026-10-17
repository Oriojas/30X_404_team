# Requisitos — Fase 2: Ingesta idempotente en todos los canales

> Rama: `feat/ingesta-idempotente` · Fase 2 de [roadmap.md](../roadmap.md) (F2.1 a F2.7).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

Hoy cada entrega crea una factura nueva. Telegram reintenta el webhook si no recibe `200` a tiempo (y el OCR con Gemini puede tardar varios segundos), y en la web un doble clic o un reintento de red vuelve a subir el mismo archivo. El resultado es una segunda factura en el Audit Log, un segundo aviso al canal y, en el peor caso, un rechazo INTEG-01 contra la propia factura original que confunde al aprobador.

`ProcessInvoiceUseCase` (`backend/app/core/use_cases/process_invoice.py`) es el único punto de entrada de los canales, así que la idempotencia se resuelve ahí, con un puerto genérico que sirve también para los canales futuros (correo con `Message-ID`, WhatsApp).

Se trabaja en dos niveles:

1. **Transporte:** la misma entrega repetida, identificada por el id propio del canal (`update_id` de Telegram, header `Idempotency-Key` en web y API). Se procesa una sola vez y la repetición devuelve la factura existente sin reprocesar ni volver a notificar.
2. **Negocio:** la misma factura enviada por mensajes distintos (otro canal, otro update). La frena INTEG-01, reforzada con el SHA-256 del archivo para que funcione aunque el OCR no lea número ni monto.

## Alcance

**Entra (F2.1 a F2.7 completas):**
- Tabla `ingested_messages` y columna `invoices.file_sha256` en `schema.sql`, idempotentes.
- Puerto `IngestionLog` en `core/ports/outbound.py` y su adaptador PostgreSQL.
- `ProcessInvoiceUseCase.from_document` y `from_extracted` aceptan un `external_id` opcional.
- Webhook de Telegram con `update_id`; `POST /api/invoices/upload` y `POST /api/invoices` con el header `Idempotency-Key`.
- Cálculo del SHA-256 del documento, persistencia y corto circuito por hash duplicado antes del OCR.
- Pruebas unitarias (fakes) y un caso en la integración con PostgreSQL.
- Actualizar `backend/README.md` (header `Idempotency-Key` y respuestas `200`/`409`) y marcar F2.x en el roadmap.

**No entra:**
- Cambios en el frontend: generar y enviar el `Idempotency-Key` es F3.5.
- Validar que una clave repetida venga con el mismo cuerpo (huella del payload). Una clave reutilizada con otro archivo devuelve la factura original.
- Expiración o limpieza programada de `ingested_messages`.
- Canales nuevos (correo, WhatsApp).
- Cambios en la matriz de reglas, salvo el texto de la explicación de INTEG-01 por hash.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **Reclamo atómico en la base.** `claim(channel, external_id)` hace `INSERT ... ON CONFLICT DO NOTHING RETURNING` sobre `PRIMARY KEY (channel, external_id)`. Solo la solicitud que inserta procesa; las demás leen el registro existente. | Resuelve la concurrencia sin locks en memoria y funciona con varias réplicas. |
| D2 | **Estados del registro:** `PROCESSING` al reclamar, `COMPLETED` con `invoice_id` al terminar. Si el procesamiento lanza una excepción, `release` borra la fila para que el reintento sí procese. | Un fallo transitorio (Gemini caído, red) no debe dejar la entrega bloqueada para siempre. |
| D3 | **Repetición con la entrega aún en proceso** (`PROCESSING`, sin factura): la API responde **`409`** con `"La factura con esta Idempotency-Key aún se está procesando."`; el cliente reintenta con la misma clave. Telegram responde **`200 {"status": "duplicate"}`** para que deje de reintentar. | Elegido por el equipo: simple, sin esperas activas, y Telegram nunca recibe un error que dispare más reintentos. |
| D4 | **Repetición de una entrega completada:** la API responde **`200`** con la misma factura (en vez de `201`). Telegram responde `200 {"status": "duplicate", "decision": ...}`. Ninguna de las dos vuelve a llamar a `notify_received` ni a `notify_decision`. | Criterio del roadmap: ni una segunda factura ni un aviso duplicado. |
| D5 | **Reclamos colgados:** si un registro sigue en `PROCESSING` más de `INGESTION_STALE_SECONDS = 300` (constante en el adaptador), un nuevo `claim` lo retoma (`ON CONFLICT DO UPDATE ... WHERE status = 'PROCESSING' AND received_at < now() - interval`). | Si el proceso muere a mitad (reinicio en Railway), la clave no queda bloqueada para siempre. Una sola consulta, sin jobs. |
| D6 | **Espacio de nombres por canal:** `channel` es `TELEGRAM` (con `update_id`), `WEB` (subida, con `Idempotency-Key`) y `API` (carga manual, con `Idempotency-Key`). El header es opcional: sin él, la solicitud se procesa como hoy. | La misma clave en dos endpoints distintos son entregas distintas; mantiene compatibilidad con el dashboard actual mientras llega F3.5. |
| D7 | **El hash se calcula en el Core** con `hashlib.sha256` (librería estándar) dentro de `from_document`, así cualquier canal que entregue un archivo queda cubierto sin repetir código en los adaptadores. | El Core solo depende de la librería estándar; un único lugar para todos los canales. |
| D8 | **Hash duplicado corta antes del OCR.** Si existe una factura no rechazada con el mismo `file_sha256` dentro de `duplicate_check_days`, no se llama a Gemini: se reutilizan los datos extraídos de la factura original y la tubería la **rechaza por INTEG-01** con la explicación "archivo idéntico a la factura #N". La nueva factura sí se guarda (con su hash) y sí se notifica, porque es una entrega de negocio distinta. | Elegido por el equipo: ahorra la llamada al modelo y deja la trazabilidad completa en el Audit Log. |
| D9 | **El reclamo envuelve todo el flujo.** Orden en `from_document`: `claim` → (si repetido, devolver) → `notify_received` → hash → OCR → tubería → `save` → `complete`. Cualquier excepción antes de `complete` hace `release` y se vuelve a lanzar. | La repetición no dispara ni el aviso de "recibido". |
| D10 | **Retorno del caso de uso:** `IngestionResult(invoice: Optional[ProcessedInvoice], duplicate: bool, in_progress: bool)` en `core/domain/models.py`. Los adaptadores de entrada traducen a `201`/`200`/`409` o al JSON de Telegram. | El Core no conoce HTTP; cada canal decide su respuesta. |

## Esquema

```sql
CREATE TABLE IF NOT EXISTS ingested_messages (
    channel      VARCHAR(20)  NOT NULL,
    external_id  VARCHAR(200) NOT NULL,
    invoice_id   INTEGER REFERENCES invoices(id),
    status       VARCHAR(20)  NOT NULL DEFAULT 'PROCESSING',
    received_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (channel, external_id)
);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS file_sha256 CHAR(64);
CREATE INDEX IF NOT EXISTS idx_invoices_file_sha256 ON invoices (file_sha256);
```

## Puerto

```python
class IngestionLog(Protocol):
    async def claim(self, channel: str, external_id: str) -> Optional[IngestionRecord]: ...
    # None si este llamado ganó el reclamo; si no, el registro existente (status, invoice_id)
    async def complete(self, channel: str, external_id: str, invoice_id: int) -> None: ...
    async def release(self, channel: str, external_id: str) -> None: ...
```

`InvoiceRepository` suma `find_by_file_hash(sha256, within_days) -> Optional[ProcessedInvoice]` (solo estados no rechazados, igual que `exists_duplicate`).

## Restricciones de arquitectura

- `IngestionLog` vive en `core/ports`; el adaptador en `adapters/outbound/db`; se cablea solo en `container.py`.
- Los adaptadores de entrada no importan el adaptador de PostgreSQL ni conocen `ingested_messages`.
- `tests/test_architecture.py` debe seguir verde.
- Imports absolutos; ninguna variable de entorno nueva.
