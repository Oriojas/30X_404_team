# Plan — Tesorería real en el dashboard

> Rama: `fix/tesoreria-real`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).

## 1. Endpoint de tesorería (backend, T1)

1.1. `app/core/use_cases/query_treasury.py`: `month_start()` y `GetTreasuryUseCase(treasury, invoices, company_id)`, que devuelve `TreasuryStatus` con `month_spent_usd` (D1, D2).
1.2. `ProcessInvoiceUseCase` usa `month_start()` en lugar de calcular el inicio de mes por su cuenta.
1.3. `TreasuryResponse` en `schemas.py`, router `api/routers/treasury.py` con `GET /api/treasury`, dependencia `get_get_treasury` y registro en `main.py`.
1.4. `Container`: un solo `PostgresTreasuryRepository`, compartido por la tubería y `GetTreasuryUseCase`.
1.5. Pruebas: `tests/test_treasury_api.py` (suma solo lo aprobado) y una aserción de `/api/treasury` en `test_postgres_integration.py`.
1.6. `backend/README.md`: agregar el endpoint a la tabla.

## 2. Cliente y estado (frontend, T2)

2.1. `api.js`: `DEFAULT_RULES.min_treasury_buffer_usd = 1000`, `DEFAULT_TREASURY` (D4), `getTreasury()`, `treasuryHeadroom()` (D3) y `formatUsd()`.
2.2. `App.jsx`: estado `treasury` cargado junto con las reglas al abrir la página; se pasa al hero y a `RuleControls`.

## 3. Hero y tarjeta de colchón (frontend, T3)

3.1. `HeroSection.jsx` recibe `treasury` y `rules`: caja, colchón, umbral autónomo, barra y "Liquidez N % OK/bajo el colchón".
3.2. `RuleControls.jsx` recibe `treasury`: "Caja" real y holgura calculada con el valor del campo de reserva (D5); barra y color según el resultado.

## 4. Verificación y cierre

4.1. `pytest` y `npm run build`.
4.2. Integración contra PostgreSQL 16 desechable con `TEST_DATABASE_URL`.
4.3. Recorrido en el navegador con backend local y seed (checklist de [validation.md](validation.md)).
4.4. Tras el merge: comprobar el dashboard público y marcar el roadmap.
