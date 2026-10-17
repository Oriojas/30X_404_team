# Validación — Tesorería comprometida

> La rama `feat/tesoreria-comprometida` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, de integración con PostgreSQL y del recorrido local en el navegador.
> Criterio: el agente nunca aprueba solo un pago que deje lo comprometido por encima del saldo o del presupuesto, ni siquiera con ingestas simultáneas, y cada pago que una persona aprueba fuera de esos límites queda registrado como excepción aprobada por ella.

## Criterios bloqueantes

### Código y pruebas (CI)

- [ ] `pytest` en `backend/` verde en el CI de F5.7, con las pruebas nuevas de la Fase 6.
- [ ] Cinco facturas de $1,900 (proveedor con historial, dentro de tarifa y umbral) con $8,500 de saldo y $1,000 de colchón: las tres primeras `AUTO_APPROVED` (disponible $2,800) y la cuarta y la quinta escalan por FIN-03 ($2,800 − $1,900 queda bajo el colchón); lo comprometido nunca supera el saldo.
- [ ] El historial del seed anterior a la foto no compromete nada: TC-01 sale `AUTO_APPROVED`.
- [ ] La explicación de FIN-01 y FIN-03 cita saldo de la foto, comprometido y disponible.
- [ ] Aprobar TC-05 desde el caso de uso deja `HUMAN_APPROVED` y el Audit Log registra el disponible y las alertas FIN vigentes como excepción aprobada por esa persona.
- [ ] Aprobar una factura INTEG-04 (`usd_amount = 0`) responde `409` y la factura sigue en `SCALED_TO_HUMAN`; rechazarla sí funciona.
- [ ] Dos ingestas concurrentes de $4,000 con $8,500 de saldo y $1,000 de colchón: exactamente una `AUTO_APPROVED`.
- [ ] `PATCH /api/treasury` con `balance_usd` válido devuelve la tesorería con `committed_usd = 0` y `snapshot_at` nuevo; con `0`, negativo o sin campo responde `422`; con `monthly_budget_usd` en el cuerpo no cambia el presupuesto.
- [ ] Las pruebas que construían `DecideInvoiceUseCase(invoices, notifier)` están adaptadas; la prueba de arquitectura sigue en verde (el candado es `asyncio.Lock` de la librería estándar; el Core no importa FastAPI ni adaptadores).
- [ ] `npm run build` en `frontend/` sin errores.

### Integración con PostgreSQL 16 (local, Docker)

- [ ] `test_postgres_integration.py` verde con `TEST_DATABASE_URL`.
- [ ] Lo comprometido suma `AUTO_APPROVED` por `processed_at` y `HUMAN_APPROVED` por `decided_at`, solo después de `updated_at`.
- [ ] FIN-02 cuenta un `HUMAN_APPROVED` en el mes de su `decided_at`, no en el de su `processed_at`.
- [ ] `updated_at` queda en UTC tras `schema.sql`, `seed.sql` y el `PATCH` (sin desfase de la zona del servidor).
- [ ] `schema.sql` y `seed.sql` siguen siendo idempotentes (se pueden correr dos veces).

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [ ] `casos_demo.py` toma una foto nueva y TC-01 a TC-07 dan el resultado esperado; una segunda corrida seguida da lo mismo.
- [ ] El hero muestra el disponible, el saldo de la foto y lo comprometido de `GET /api/treasury`.
- [ ] Tras una factura `AUTO_APPROVED` o una aprobación desde el Drawer, el hero baja el disponible sin recargar la página.
- [ ] La tarjeta de presupuesto muestra presupuesto mensual, gasto del mes y restante, y coincide con la respuesta del endpoint.
- [ ] Aprobar TC-05 desde el Drawer muestra en el Audit Log la excepción con el disponible.
- [ ] Aprobar una factura INTEG-04 desde el Drawer muestra el mensaje del `409` y la factura sigue escalada.
- [ ] Con la API viva pero `GET /api/treasury` fallando, el hero y las tarjetas muestran "—"; con la API caída, banner de demostración y valores del seed.
- [ ] Sin errores de JavaScript en la consola.

## Después del merge (producción)

- [ ] `humo_produccion.py` verde contra producción, con la foto tomada antes de TC-01.
- [ ] El dashboard público muestra el disponible y el presupuesto del mismo `GET /api/treasury` con que decide el agente.
- [ ] F6.1 a F6.6 marcados en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## No bloqueante

- Variante estricta de la revalidación (F9.7) y prueba de aprobaciones concurrentes (F9.8).
- Varias réplicas (`pg_advisory_xact_lock`).
