# Requisitos — Tesorería comprometida

> Rama: `feat/tesoreria-comprometida` · Fase 6 de [roadmap.md](../roadmap.md) (F6.1 a F6.6).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

El reto descalifica a quien apruebe un pago indebido, y el principio 1 de [mission.md](../mission.md) exige tolerancia cero. Hoy la Capa 3 (Solvencia) tiene tres huecos:

- **Cada factura se evalúa sola contra el saldo total.** `_solvency` en `rules_pipeline.py` compara `usd_amount` con `TreasuryStatus.balance_usd`, que nunca baja. Con $8,500 de caja y $1,000 de colchón, cinco facturas de $1,900 de proveedores con historial salen `AUTO_APPROVED` aunque suman $9,500.
- **La aprobación humana no revisa la solvencia.** `DecideInvoiceUseCase` solo recibe `InvoiceRepository` y el notificador: pasa la factura a `HUMAN_APPROVED` sin mirar cuánto queda disponible ni dejarlo en el Audit Log.
- **Las ingestas concurrentes leen el mismo saldo.** Telegram y la web pueden evaluar a la vez; las dos leen el mismo disponible y las dos pueden aprobarse.

Además, FIN-02 suma el gasto del mes por `processed_at`, que en un `HUMAN_APPROVED` es la fecha de ingesta y no la de aprobación.

## Alcance

**Entra (F6.1 a F6.6, en una sola rama):**
- Saldo como foto con fecha (`treasury_accounts.updated_at`) y comprometido = aprobado después de la foto.
- `PATCH /api/treasury` con el saldo (toma una foto nueva).
- FIN-01 y FIN-03 contra el disponible; FIN-02 con la fecha de aprobación.
- Revalidación de la Capa 3 al aprobar desde el dashboard, registrada en el Audit Log; `409` al aprobar una factura INTEG-04.
- Un solo `asyncio.Lock` que serializa lectura de tesorería, evaluación y guardado.
- `GET /api/treasury` con `committed_usd`, `available_usd` y `snapshot_at`; hero con el disponible y tarjeta de presupuesto y gasto del mes.
- `casos_demo.py` y `humo_produccion.py` toman una foto nueva antes de TC-01.
- Pruebas unitarias, de concurrencia e integración con PostgreSQL 16; README del backend.

**No entra:**
- Editar el presupuesto mensual (F7.1). El `PATCH` de esta fase acepta **solo** `balance_usd`.
- Rechazar con `409` una aprobación por una alerta FIN nueva (variante estricta, F9.7).
- Prueba de dos aprobaciones simultáneas (F9.8; el candado ya las serializa).
- `pg_advisory_xact_lock` o soporte de varias réplicas.
- Migrar las fechas a `TIMESTAMPTZ` (después del Demo Day).
- Autenticación del `PATCH` (Fase 8).
- Estado de pago ejecutado: el reto no mueve dinero.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **Saldo como foto con fecha:** `balance_usd` es el saldo a la fecha de `updated_at`. `committed_usd = Σ usd_amount` de `AUTO_APPROVED` con `processed_at > updated_at` y de `HUMAN_APPROVED` con `decided_at > updated_at`. `available_usd = balance_usd − committed_usd`. | Sin pagos ejecutados, es la única forma de que lo aprobado descuente sin que el historial del seed (anterior a la foto) bloquee TC-01. |
| D2 | **`PATCH /api/treasury` solo con `balance_usd`** (`> 0`, si no `422`). Actualiza el saldo y `updated_at`, lo que libera lo comprometido. El presupuesto queda para F7.1. | Decisión del 17-oct-2026: alcance mínimo; F7.1 agrega el presupuesto con su propia validación. |
| D3 | **UTC en todas las escrituras de `updated_at`:** `DEFAULT timezone('UTC', now())` en `schema.sql`, el seed y el `UPDATE`. | Las fechas de las facturas se guardan en UTC sin zona (F5.8); comparar contra una hora local correría la ventana. |
| D4 | **Fecha de aprobación única:** `processed_at` en `AUTO_APPROVED`, `decided_at` en `HUMAN_APPROVED`, tanto para lo comprometido (D1) como para el gasto del mes (FIN-02). Una sola consulta en `PostgresTreasuryRepository.get`. | Una sola fuente para la Capa 3 y el dashboard, como D2 de la Fase 4.1. |
| D5 | **FIN-01 y FIN-03 contra el disponible**, y la explicación cita saldo, comprometido y disponible. `TreasuryStatus` gana `committed_usd` y `snapshot_at`, con `available_usd` derivado. | El Audit Log debe explicar por qué escaló sin leer código (principio 3). |
| D6 | **La persona siempre puede aprobar**, salvo INTEG-04 (`usd_amount = 0`), que responde `409`. Antes de `HUMAN_APPROVED`, `DecideInvoiceUseCase` recalcula la Capa 3 con `TreasuryRepository` y `RulesRepository` y agrega al Audit Log el disponible y las alertas FIN vigentes como excepción aprobada por esa persona. | La aprobación humana es la vía de excepción del reto; lo que no puede pasar es aprobar a ciegas ni comprometer $0 por un monto desconocido. |
| D7 | **Un solo `asyncio.Lock`** creado en `container.py` e inyectado en `ProcessInvoiceUseCase` (solo `_evaluate` + guardado, el OCR fuera), `DecideInvoiceUseCase` y el `PATCH`. La limitación (una réplica en Railway) queda en el README. | Evita que dos evaluaciones lean el mismo disponible sin bloquear el OCR, que es lo lento. |
| D8 | **Hero con el disponible y tarjeta de presupuesto:** el hero muestra disponible, saldo de la foto y comprometido; una tarjeta nueva muestra presupuesto mensual, gasto del mes y restante. Con la API viva y `GET /api/treasury` fallando se muestra "—" (D4 de la Fase 4.1). | El jurado ve en el dashboard el mismo número con el que decide el agente. |
| D9 | **Los scripts de demo toman una foto antes de TC-01:** `casos_demo.py` y `humo_produccion.py` llaman `PATCH /api/treasury` con $8,500. | Sin eso, las aprobaciones de corridas anteriores en producción comprometen el saldo y TC-01 escalaría. |
