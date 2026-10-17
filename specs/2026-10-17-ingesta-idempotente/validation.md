# Validación — Fase 2: Ingesta idempotente en todos los canales

> La rama `feat/ingesta-idempotente` se puede mergear cuando se cumplen **todos** los criterios bloqueantes.
> Criterio del roadmap: repetir una entrega por cualquier canal no crea una segunda factura ni un aviso duplicado, y el mismo archivo enviado por otro canal queda frenado por INTEG-01.

## Criterios bloqueantes

> Verificado el 17-oct-2026 en `feat/ingesta-idempotente`: 64 pasadas (6 omitidas) sin `TEST_DATABASE_URL` ni red; 70 de 70 con PostgreSQL 16 en Docker, tres corridas seguidas sobre la misma base.

### Pruebas automáticas (fakes, sin red)

- [x] `pytest` en `backend/` pasa completo, incluido `tests/test_architecture.py`, sin `GEMINI_API_KEY` ni internet.
- [x] **Telegram:** el mismo `update_id` dos veces → una sola factura, un solo `notify_received` y un solo `notify_decision`; la segunda respuesta es `200 {"status": "duplicate"}` y el archivo no se vuelve a descargar.
- [x] **Telegram en proceso:** un `update_id` reclamado y sin terminar → `503`, sin descargar. Si la primera entrega libera la clave, el reintento sí se procesa.
- [x] **Aviso después de guardar:** si `notify_decision` falla, la entrega queda `COMPLETED` y el reintento devuelve la misma factura.
- [x] **Cancelación:** una solicitud cancelada a mitad del OCR libera la clave.
- [x] **Web y API:** la misma `Idempotency-Key` dos veces en `/upload` y en `POST /api/invoices` → `201` y luego `200` con el mismo `id`.
- [x] **En proceso:** una clave reclamada sin factura → `409` con el mensaje "aún se está procesando".
- [x] **Sin header:** dos subidas sin `Idempotency-Key` crean dos facturas (comportamiento actual intacto).
- [x] **Espacio de nombres:** la misma clave en `/upload` y en `POST /api/invoices` no colisiona.
- [x] **Reintento tras fallo:** si el OCR o la tubería lanzan excepción, la clave se libera y el reintento con la misma clave sí procesa.
- [x] **Concurrencia:** dos solicitudes simultáneas con la misma clave → exactamente una factura y un aviso.
- [x] **Hash entre canales:** el mismo archivo por Telegram y luego por web (claves distintas) → la segunda factura queda `REJECTED` por INTEG-01, el OCR se llamó **una sola vez** y la explicación cita la factura original.
- [x] **Hash sin texto legible:** un archivo con extracción vacía (confianza 0) repetido igual queda frenado por INTEG-01 en la segunda entrega.
- [x] **Bordes del hash:** si la factura original está `REJECTED` o fuera de `duplicate_check_days`, el archivo se procesa normalmente.
- [x] Las pruebas existentes de INTEG-01 (por número/monto), de la tubería y del OCR siguen verdes sin cambios de expectativa.

### Integración con PostgreSQL (`TEST_DATABASE_URL`)

- [x] `schema.sql` corre dos veces seguidas sin error sobre una base que ya tiene datos.
- [x] `claim` concurrente desde dos conexiones: solo una gana.
- [x] `complete` guarda `invoice_id`; `release` borra el reclamo; un reclamo en `PROCESSING` con más de 300 s se puede retomar.
- [x] `find_by_file_hash` encuentra la factura por hash y respeta la ventana y los estados.
- [x] Flujo completo con seed: una subida con `Idempotency-Key` repetida → una fila en `invoices` y una en `ingested_messages` en `COMPLETED`.

### Código y arquitectura

- [x] `IngestionLog` está en `app/core/ports` y su adaptador en `app/adapters/outbound/db`; solo `container.py` los conecta.
- [x] El Core solo usa la librería estándar (`hashlib`) para el hash; ningún adaptador de entrada importa adaptadores de salida.
- [x] No hay variables de entorno nuevas; ningún módulo fuera de `app/config.py` usa `os.getenv`.
- [x] `ingested_messages` y `file_sha256` están en `schema.sql` con `IF NOT EXISTS`.

### Documentación

- [x] `backend/README.md` documenta `Idempotency-Key`, las respuestas `200`/`201`/`409` y la respuesta `duplicate` del webhook.
- [x] `specs/roadmap.md` tiene F2.1 a F2.7 marcadas y `specs/tech-stack.md` refleja el estado final.

## Verificación recomendada (no bloquea el merge)

- [ ] Con el backend en Docker + PostgreSQL, repetir con `curl` una subida con la misma `Idempotency-Key` y confirmar `201` → `200` y una sola fila en el Audit Log.
- [ ] Reenviar a mano un update de Telegram al webhook (mismo cuerpo JSON) y confirmar que el chat recibe un solo aviso.
- [ ] Subir por la web un fixture ya enviado por Telegram y confirmar el rechazo INTEG-01 en el dashboard.

## Cómo correr

```bash
cd backend && pytest -q
```

```bash
cd backend && TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/paybot_test pytest -q tests/test_postgres_integration.py
```
