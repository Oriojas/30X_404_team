# Validación — Validaciones pendientes, casos trampa y CI

> La rama `feat/fase-5-validaciones-ci` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, CI y producción.
> Criterio: las verificaciones recomendadas de las Fases 2 a 4 quedan marcadas con evidencia, la demo cubre los casos trampa que ya permite el código y cada PR muestra el resultado de las pruebas.

## Criterios bloqueantes

### Código y pruebas

- [x] `pytest` en `backend/` verde (integración omitida sin `TEST_DATABASE_URL`), incluida la prueba unitaria de TC-07: solo INTEG-02, sin HITL-03. *(71 pasadas, 6 omitidas)*
- [x] `tests/test_postgres_integration.py` contra PostgreSQL 16 con seed en Docker: TC-01 a TC-07 dan lo esperado (TC-07 `SCALED_TO_HUMAN` con `INTEG-02` en `audit_explanation`). *(6 pasadas, 17-oct-2026)*
- [x] La prueba de arquitectura sigue en verde y el Core no cambió.
- [x] `npm run build` en `frontend/` sin errores.
- [x] TC-07 aparece en `casos_demo.py`, en la Test Suite de [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md), en `backend/README.md`, en `seed.sql` (la fila de AWS marca que TC-07 depende de su tarifa), en [mission.md](../mission.md) y en el guion del pitch; ningún texto vigente dice "TC-01 a TC-06" donde ya corren siete casos. Las fases cerradas de [roadmap.md](../roadmap.md) (F0.3, F3.6) conservan su texto histórico.

### CI

- [x] `.github/workflows/ci.yml` corre en el PR de esta rama con los jobs `backend` y `frontend`, y ambos quedan en verde. *(PR #17: verde en `2003c9e` y `313e233`; también en el push a `master`, `379fef5`)*
- [x] El workflow no usa secretos ni servicios externos; el log de `pytest` muestra las pruebas de integración como omitidas.
- [x] [tech-stack.md](../tech-stack.md) menciona GitHub Actions.

### Producción (Fases 2 a 4)

- [x] **F5.1:** una factura enviada como documento por Telegram aparece en el dashboard público, se aprueba desde el Drawer y el chat recibe el aviso del resultado. *(Fase 5, F5.1, 17-oct-2026, en producción: `factura_nube_andina.pdf` enviada como documento por Telegram → factura 21, NA-4521, `SCALED_TO_HUMAN` por HITL-01; aprobada desde el Drawer del dashboard público por "CFO Demo" con nota; el chat recibió "✅ Pago aprobado por un operador · Factura #NA-4521 · $3,000.00 USD" con la explicación y la nota.)*
- [x] **F5.2:** el reenvío con `curl` del mismo `update_id` al webhook de producción responde `200 {"status": "duplicate"}`; el chat no recibe un segundo aviso y no aparece otra factura. *(Fase 5, F5.2, 17-oct-2026, en producción: `POST /api/webhook/telegram` con el secret y el `update_id` 239648102 de la factura 21 → `200 {"status": "duplicate", "decision": "HUMAN_APPROVED"}`; no apareció otra factura y el chat no recibió aviso. El cuerpo llevó `chat_id` 0 y un `file_id` ficticio: la deduplicación por `update_id` ocurre antes de avisar y de descargar, así que una repetición no toca el chat ni Telegram.)*
- [x] **F5.3:** el mismo archivo subido por la web queda `REJECTED` por INTEG-01 en el dashboard. *(Fase 5, F5.3, 17-oct-2026, en producción: el mismo `factura_nube_andina.pdf` subido por `POST /api/invoices/upload` (el endpoint del botón de subida, canal `WEB`, con `Idempotency-Key`) → `201`, factura 22, `REJECTED` por INTEG-01 "el archivo es idéntico a la factura #21"; visible así en el Audit Log del dashboard. El botón no se pulsó porque el selector de archivos del sistema no se puede automatizar.)*
- [x] **F5.4:** el `201` → `200` de `Idempotency-Key` y el build con `frontend/Dockerfile` están marcados en sus `validation.md` con la referencia a la evidencia de la Fase 4. *(el humo del 17-oct-2026 en producción dio 10/10: `200` en TC-01 a TC-06 y `201` en TC-07, factura 20)*
- [x] Los ítems pendientes de [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) y [frontend-api-real/validation.md](../2026-10-17-frontend-api-real/validation.md) quedan marcados, cada uno con su evidencia.
- [x] Ningún secreto aparece en el repo, en el workflow ni en la evidencia registrada.

### Fechas en UTC (F5.8)

- [x] `GET /api/invoices` serializa `processed_at` y `decided_at` en UTC con `Z`; `tests/test_schemas_fechas.py` en verde. *(73 pasadas, 6 omitidas)*
- [x] `AuditTable.jsx` y `AuditDrawer.jsx` leen las fechas con `parseApiDate`; `npm run build` sin errores.
- [ ] Tras el deploy, en el dashboard público una factura recién creada muestra "Hace un momento" o "Hace N min", no "Hace 7 horas" (navegador en GMT+7).

### Datos para el pitch

- [x] Arranque en frío medido según D6 (segundos desde el redeploy hasta `database: connected`, con fecha) y anotado en [presentacion_y_guion.md](../../docs/pitch_presentacion/presentacion_y_guion.md). *(17-oct-2026: redeploy activo en 25 s; el contenedor arranca en 0.7 s y el primer healthcheck responde a los 0.9 s)*
- [x] Captura del dashboard público guardada en `docs/pitch_presentacion/`. *(`dashboard_produccion_hero.jpg` y `dashboard_produccion_audit_log.jpg`)*

## Después del merge (producción)

- [x] `humo_produccion.py` contra producción pasa con TC-07 incluido. *(10/10 el 17-oct-2026; TC-07 = factura 20, `SCALED_TO_HUMAN` por INTEG-02)*
- [x] F5.1 a F5.7 marcadas en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## Hallazgos

- **Fechas del Audit Log desfasadas por zona horaria:** la API devuelve `processed_at` y `decided_at` sin zona (`2026-10-17T12:41:01`, en UTC), y `AuditTable.jsx` y `AuditDrawer.jsx` los leen con `new Date(iso)` como hora local. En un navegador en GMT+7 una factura recién creada aparece como "Hace 7 horas"; en Colombia (GMT-5) quedaría 5 horas en el futuro. No afecta las decisiones, pero se ve en la demo. Se corrige en F5.8 (D9).

## No bloqueantes

- Exigir el check del CI con protección de rama en `master` (configuración del repositorio que decide el equipo).
- PostgreSQL en el CI (F9.6).
- TC-08 de presupuesto insuficiente (F7.6).
