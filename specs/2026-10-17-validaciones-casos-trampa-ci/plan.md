# Plan — Validaciones pendientes, casos trampa y CI

> Rama: `feat/fase-5-validaciones-ci`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).
> Los grupos 1 y 2 son código y se pueden hacer primero; los grupos 3 y 4 tocan producción.

## 1. TC-07: no cuadra con lo acordado (F5.5)

1.1. `backend/scripts/casos_demo.py`: agregar TC-07 a `CASOS` con el payload de D1 (`SCALED_TO_HUMAN`, `INTEG-02`) y actualizar el docstring a "TC-01..TC-07".
1.2. `backend/scripts/humo_produccion.py`: actualizar el docstring y cualquier conteo fijo de casos.
1.3. `test_postgres_integration.py`: confirmar que recorre TC-07 sin cambios (D2) y ajustar los conteos que dependan del número de facturas creadas.
1.4. Prueba unitaria con fakes en `test_rules_pipeline.py` o `test_process_invoice.py`: proveedor con historial, monto sobre la tarifa pactada y bajo el umbral → solo INTEG-02, sin HITL-03.
1.5. Test Suite de [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md): fila TC-07; `backend/README.md` pasa de "TC-01..TC-06" a "TC-01..TC-07".

## 2. CI en GitHub Actions (F5.7)

2.1. `.github/workflows/ci.yml` con los jobs `backend` y `frontend` de D7.
2.2. Correr en local los mismos comandos (`pytest` en `backend/`, `npm ci && npm run build` en `frontend/`) antes del push.
2.3. [tech-stack.md](../tech-stack.md): mencionar GitHub Actions en la fila de pruebas (D8).
2.4. Abrir el PR y confirmar que el workflow corre y queda verde.

## 3. Verificaciones en producción (F5.1 a F5.4)

3.1. **Preparación:** `railway variables` para leer `TELEGRAM_WEBHOOK_SECRET` y la URL de la base de datos en la sesión (no se guardan); `humo_produccion.py` contra producción para partir de un estado sano.
3.2. **F5.1 (humano + Claude):** el equipo envía un fixture como **documento** al bot desde Telegram (D5). Claude abre el dashboard público en el navegador integrado, pulsa Actualizar, localiza la factura escalada y la aprueba desde el Drawer con una nota. El equipo confirma que el chat recibió el aviso del resultado (captura del chat).
3.3. **F5.2:** leer el `update_id` de la factura de 3.2 en `ingested_messages`; reenviar con `curl` al webhook de producción el cuerpo de D4 con el secret; esperar `200 {"status": "duplicate"}`. El equipo confirma que no llegó un segundo aviso; la base sigue con una sola factura para ese archivo.
3.4. **F5.3:** subir por la web del dashboard el mismo fixture de 3.2; esperar `REJECTED` por INTEG-01 en el Audit Log y en el Drawer.
3.5. **F5.4:** marcar en [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) el `201` → `200` con referencia a la segunda corrida de `humo_produccion.py` de la Fase 4, y en [frontend-api-real/validation.md](../2026-10-17-frontend-api-real/validation.md) el build con `frontend/Dockerfile` con referencia al servicio de Railway (F4.4).
3.6. Registrar la evidencia de 3.2 a 3.4 (ids de factura, respuestas, fecha) en los `validation.md` de origen y en el [validation.md](validation.md) de esta fase.

## 4. Datos para el pitch (F5.6)

4.1. `railway redeploy` del backend y medir el arranque en frío según D6 (un bucle de `curl` a `/api/health` con marca de tiempo).
4.2. Captura del dashboard público en producción (hero con la tesorería real y el Audit Log con TC-01 a TC-07) con el navegador integrado.
4.3. Anotar ambos datos en [presentacion_y_guion.md](../../docs/pitch_presentacion/presentacion_y_guion.md) y guardar la captura en `docs/pitch_presentacion/`.

## 5. Fechas en UTC (F5.8, hallazgo de producción)

5.1. `backend/app/adapters/inbound/api/schemas.py`: `field_serializer` de `processed_at` y `decided_at` en `InvoiceResponse` que emite UTC con `Z` (D9).
5.2. `backend/tests/test_schemas_fechas.py`: una fecha sin zona sale con `Z`, una con zona se convierte a UTC y la ausente sigue nula.
5.3. `frontend/src/api.js`: `parseApiDate`; `AuditTable.jsx` (hora relativa) y `AuditDrawer.jsx` (fecha de la decisión) la usan en vez de `new Date(iso)`.
5.4. `pytest`, `npm run build` y, tras el deploy, el dashboard público muestra "Hace un momento" o "Hace N min" en una factura recién creada.

## 6. Cierre

6.1. Tras el merge: `humo_produccion.py` contra producción con TC-07 (ya desplegado).
6.2. Marcar F5.1 a F5.8 en [roadmap.md](../roadmap.md) con la referencia a esta validación.
