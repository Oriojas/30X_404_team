# Plan — Tesorería real en el dashboard

> Rama: `fix/tesoreria-real`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).

## 1. Endpoint de tesorería (backend, T1)

1.1. `PostgresTreasuryRepository.get` devuelve `TreasuryStatus` con `month_spent_usd` (acumulado aprobado desde el 1.º del mes en UTC) en una sola consulta; se quita `sum_approved_usd_since` del puerto `InvoiceRepository` (D2).
1.2. `ProcessInvoiceUseCase` deja de sumar por su cuenta: usa el `month_spent_usd` que trae la tesorería.
1.3. `app/core/use_cases/query_treasury.py`: `GetTreasuryUseCase(treasury, company_id)` (D1).
1.4. `TreasuryResponse.from_domain` en `schemas.py`, router `api/routers/treasury.py` con `GET /api/treasury`, dependencia `get_get_treasury` y registro en `main.py`.
1.5. `Container`: un solo `PostgresTreasuryRepository`, compartido por la tubería y `GetTreasuryUseCase`.
1.6. Pruebas: `tests/test_treasury_api.py` (forma de la respuesta) y, en `test_postgres_integration.py`, la ventana del mes (las aprobadas del seed de hace 35 a 50 días no cuentan) y la suma de `AUTO_APPROVED` + `HUMAN_APPROVED`.
1.7. `backend/README.md`: agregar el endpoint a la tabla.

## 2. Cliente y estado (frontend, T2)

2.1. `api.js`: `DEFAULT_RULES.min_treasury_buffer_usd = 1000`, `DEFAULT_TREASURY` (D4), `getTreasury()`, `treasuryHeadroom()` (D3), `headroomText()`, `headroomColor()` y `formatUsd()`.
2.2. `App.jsx`: estado `treasury` (`null` hasta que responde la API) cargado junto con las reglas; el seed solo se usa en modo demostración (D4).

## 3. Hero y tarjeta de colchón (frontend, T3)

3.1. `HeroSection.jsx` recibe `treasury` y `rules`: caja, colchón, umbral autónomo, barra y "Liquidez N % OK/bajo el colchón".
3.2. `RuleControls.jsx` recibe `treasury`: "Caja" real y holgura calculada con el valor del campo de reserva (D5); barra y color según el resultado.

## 4. Verificación y cierre

4.1. `pytest` y `npm run build`.
4.2. Integración contra PostgreSQL 16 desechable con `TEST_DATABASE_URL`.
4.3. Recorrido en el navegador con backend local y seed (checklist de [validation.md](validation.md)).
4.4. Tras el merge: comprobar el dashboard público y marcar el roadmap.
