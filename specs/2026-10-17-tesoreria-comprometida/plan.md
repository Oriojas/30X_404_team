# Plan — Tesorería comprometida

> Rama: `feat/tesoreria-comprometida`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).

## 1. Saldo como foto con fecha (backend, F6.1)

1.1. `schema.sql`: `treasury_accounts.updated_at` con `DEFAULT timezone('UTC', now())` (idempotente: `ALTER COLUMN ... SET DEFAULT`). `seed.sql` escribe `updated_at` con la misma expresión (D3).
1.2. `TreasuryStatus` en `models.py`: agregar `committed_usd: float = 0.0` y `snapshot_at: Optional[datetime] = None`, y la propiedad `available_usd = balance_usd − committed_usd` (D5).
1.3. `PostgresTreasuryRepository.get`: una sola consulta que devuelve saldo, presupuesto, `updated_at`, lo comprometido después de la foto y el gasto del mes, ambos con la fecha de aprobación de D4 (`processed_at` en `AUTO_APPROVED`, `decided_at` en `HUMAN_APPROVED`).
1.4. Puerto `TreasuryRepository`: `set_balance(company_id, balance_usd, as_of) -> TreasuryStatus`, que actualiza saldo y `updated_at = as_of` (UTC, reloj de la app; D3). Fake equivalente en `tests/fakes.py`.
1.5. Caso de uso `UpdateTreasuryBalanceUseCase` en `query_treasury.py` (o archivo propio) y `PATCH /api/treasury` con `TreasuryBalanceUpdate` (`balance_usd > 0`, si no `422`) (D2).

## 2. Solvencia con el disponible (Core, F6.2)

2.1. `_solvency` en `rules_pipeline.py`: FIN-01 y FIN-03 contra `available_usd`; FIN-02 sin cambios de fórmula (ya usa `month_spent_usd`, ahora con la fecha de D4).
2.2. Mensajes de FIN-01 y FIN-03 con saldo de la foto, comprometido y disponible.
2.3. Pruebas en `test_rules_pipeline.py`: factura que cabe en el saldo pero no en el disponible escala por FIN-01; colchón contra el disponible por FIN-03.

## 3. Revalidación al aprobar (Core, F6.3)

3.1. `DecideInvoiceUseCase(invoices, treasury, rules, company_id, lock, notifier)`; cableado en `container.py`.
3.2. Al aprobar: si `usd_amount == 0` (INTEG-04), error de dominio → `409`. Si no, leer tesorería y reglas, evaluar la Capa 3 y agregar a la explicación el disponible y las alertas FIN vigentes como "excepción aprobada por <decided_by>" (D6). Rechazar no revalida.
3.3. Router de decisión: mapear el error nuevo a `409` con mensaje claro.
3.4. Adaptar las pruebas que construyen `DecideInvoiceUseCase(invoices, notifier)`.

## 4. Serializar la solvencia (F6.4)

4.1. `container.py` crea **un** `asyncio.Lock` y lo inyecta en `ProcessInvoiceUseCase`, `DecideInvoiceUseCase` y `UpdateTreasuryBalanceUseCase`.
4.2. `ProcessInvoiceUseCase._evaluate`: tomar el candado desde la lectura de tesorería hasta `invoices.save` (el OCR y la descarga quedan fuera).
4.3. `DecideInvoiceUseCase`: candado alrededor de la revalidación y `update_decision`; `PATCH /api/treasury`: alrededor del `UPDATE`.
4.4. `backend/README.md`: limitación de una réplica y el reemplazo por `pg_advisory_xact_lock` (D7).

## 5. Endpoint y dashboard (F6.5)

5.1. `TreasuryResponse` agrega `committed_usd`, `available_usd` y `snapshot_at` (UTC con `Z`, como F5.8). `backend/README.md`: `PATCH /api/treasury` en la tabla.
5.2. `api.js`: `DEFAULT_TREASURY` con los campos nuevos y `snapshot_at` interpretado con `parseApiDate`.
5.3. `HeroSection.jsx`: disponible como cifra principal, con saldo de la foto y comprometido; liquidez con el disponible.
5.4. `RuleControls.jsx`: la holgura del colchón usa el disponible; tarjeta nueva de presupuesto mensual, gasto del mes y restante (solo lectura, D8).
5.5. Tras aprobar o subir una factura, recargar la tesorería para que el hero refleje lo comprometido.

## 6. Scripts de demo (D9)

6.1. `casos_demo.py` (solo datos) define `SALDO_DEMO_USD = 8500`; `humo_produccion.py` y la integración llaman `PATCH /api/treasury` con ese saldo antes de TC-01.
6.2. Verificar que TC-01 a TC-07 siguen dando lo esperado en local.

## 7. Pruebas y cierre (F6.6)

7.1. Unitarias: varias facturas que caben solas pero no juntas (la que desborda escala por FIN-01); historial anterior a la foto que no compromete; aprobación humana de TC-05 registrada como excepción; `409` al aprobar una factura INTEG-04; `PATCH` libera lo comprometido; `422` con saldo inválido.
7.2. Concurrencia: dos ingestas simultáneas de $4,000 con $8,500 de saldo y $1,000 de colchón → solo una `AUTO_APPROVED`.
7.3. `test_postgres_integration.py`: comprometido con fechas UTC, FIN-02 con `decided_at`, `PATCH` mueve la foto.
7.4. `pytest` y `npm run build`; integración con PostgreSQL 16 en Docker (`TEST_DATABASE_URL`).
7.5. Recorrido en el navegador con backend local y seed (checklist de [validation.md](validation.md)).
7.6. Tras el merge: verificación en producción, marcar F6.1 a F6.6 en el roadmap con la evidencia.
