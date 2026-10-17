# Validación — Validaciones pendientes, casos trampa y CI

> La rama `feat/fase-5-validaciones-ci` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, CI y producción.
> Criterio: las verificaciones recomendadas de las Fases 2 a 4 quedan marcadas con evidencia, la demo cubre los casos trampa que ya permite el código y cada PR muestra el resultado de las pruebas.

## Criterios bloqueantes

### Código y pruebas

- [ ] `pytest` en `backend/` verde (integración omitida sin `TEST_DATABASE_URL`), incluida la prueba unitaria de TC-07: solo INTEG-02, sin HITL-03.
- [ ] `tests/test_postgres_integration.py` contra PostgreSQL 16 con seed en Docker: TC-01 a TC-07 dan lo esperado (TC-07 `SCALED_TO_HUMAN` con `INTEG-02` en `audit_explanation`).
- [ ] La prueba de arquitectura sigue en verde y el Core no cambió.
- [ ] `npm run build` en `frontend/` sin errores.
- [ ] TC-07 aparece en `casos_demo.py`, en la Test Suite de [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md) y en `backend/README.md`; ningún texto dice "TC-01..TC-06" donde ya corren siete casos.

### CI

- [ ] `.github/workflows/ci.yml` corre en el PR de esta rama con los jobs `backend` y `frontend`, y ambos quedan en verde.
- [ ] El workflow no usa secretos ni servicios externos; el log de `pytest` muestra las pruebas de integración como omitidas.
- [ ] [tech-stack.md](../tech-stack.md) menciona GitHub Actions.

### Producción (Fases 2 a 4)

- [ ] **F5.1:** una factura enviada como documento por Telegram aparece en el dashboard público, se aprueba desde el Drawer y el chat recibe el aviso del resultado. *(id de factura, captura del chat)*
- [ ] **F5.2:** el reenvío con `curl` del mismo `update_id` al webhook de producción responde `200 {"status": "duplicate"}`; el chat no recibe un segundo aviso y no aparece otra factura. *(respuesta y `update_id`)*
- [ ] **F5.3:** el mismo archivo subido por la web queda `REJECTED` por INTEG-01 en el dashboard. *(id de factura)*
- [ ] **F5.4:** el `201` → `200` de `Idempotency-Key` y el build con `frontend/Dockerfile` están marcados en sus `validation.md` con la referencia a la evidencia de la Fase 4.
- [ ] Los ítems pendientes de [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) y [frontend-api-real/validation.md](../2026-10-17-frontend-api-real/validation.md) quedan marcados, cada uno con su evidencia.
- [ ] Ningún secreto aparece en el repo, en el workflow ni en la evidencia registrada.

### Datos para el pitch

- [ ] Arranque en frío medido según D6 (segundos desde el redeploy hasta `database: connected`, con fecha) y anotado en [presentacion_y_guion.md](../../docs/pitch_presentacion/presentacion_y_guion.md).
- [ ] Captura del dashboard público guardada en `docs/pitch_presentacion/`.

## Después del merge (producción)

- [ ] `humo_produccion.py` contra producción pasa con TC-07 incluido.
- [ ] F5.1 a F5.7 marcadas en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## No bloqueantes

- Exigir el check del CI con protección de rama en `master` (configuración del repositorio que decide el equipo).
- PostgreSQL en el CI (F9.6).
- TC-08 de presupuesto insuficiente (F7.6).
