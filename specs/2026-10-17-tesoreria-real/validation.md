# Validación — Tesorería real en el dashboard

> La rama `fix/tesoreria-real` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código y del recorrido local.
> Criterio: el hero y la tarjeta de colchón muestran la misma tesorería y el mismo colchón con los que decide el agente.

## Criterios bloqueantes

### Código y pruebas

- [x] `pytest` en `backend/` verde, incluida `tests/test_treasury_api.py`. *(70 pasadas, 6 omitidas sin `TEST_DATABASE_URL`)*
- [x] `tests/test_postgres_integration.py` contra PostgreSQL 16 con seed: `/api/treasury` devuelve `balance_usd = 8500` y `monthly_budget_usd = 25000`. *(6 pasadas)*
- [x] `month_spent_usd` suma solo facturas aprobadas del mes en curso: del seed solo cuenta DS-1042 (1.200 USD, hace 3 días) y no las aprobadas de hace 35 a 50 días; tras TC-01 (`AUTO_APPROVED`, 450) y la aprobación humana de TC-04 (`HUMAN_APPROVED`, 3.500) sube 3.950. *(integración con SQL real)*
- [x] La tubería (FIN-02) y el endpoint leen el gasto del mes del mismo `TreasuryRepository.get`.
- [x] La prueba de arquitectura sigue en verde (el Core no importa FastAPI).
- [x] `npm run build` en `frontend/` sin errores.
- [x] Ningún componente conserva los valores fijos `$48,250`, `$10,000` ni `79%` en el hero o en la tarjeta de colchón. *(queda solo el chat ilustrativo de `AgentWorkflow.jsx`, fuera de alcance)*

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [x] El hero muestra "$8,500.00 USD", "Colchón protegido: $1,000 USD" y "Liquidez 88% OK"; el umbral autónomo muestra "$2,000".
- [x] La tarjeta "Colchón Mínimo Tesorería" muestra "Caja: $8,500 USD" y "Holgura 88% OK".
- [x] Al escribir 9000 en la reserva, sin guardar, la tarjeta muestra "Holgura 0% bajo el colchón" en rojo y la barra queda en 0.
- [x] Con la reserva vacía, la tarjeta muestra "Holgura —" (no "100% OK"); con 8499.99 muestra "Holgura <1% OK".
- [x] Con la API viva pero sin `GET /api/treasury` (backend de `master`, responde `404`): el hero y la tarjeta muestran "—", sin banner de demostración y sin el saldo del seed.
- [x] Con la API caída: banner de demostración y valores del seed ($8,500, $1,000, 88 %).
- [x] Sin errores de JavaScript en la consola (solo las solicitudes fallidas esperadas al apagar el backend o recibir el `404`).
- [x] Sin modo demostración: los valores vienen de `GET /api/treasury` y `GET /api/rules`.

## Después del merge (producción)

- [x] El dashboard público muestra la caja y el colchón de producción (hoy $8,500 y $1,000) en el hero y en la tarjeta. *(17-oct-2026, tras el merge de #14: "Liquidez 88% OK" en el hero y "Holgura 88% OK" en la tarjeta, sin modo demostración; en consola solo un `ERR_BLOCKED_BY_CLIENT` del navegador, ningún error de la app)*
- [x] `GET https://backend-production-ea088.up.railway.app/api/treasury` responde `200`. *(`balance_usd` 8500, `monthly_budget_usd` 25000, `month_spent_usd` 6150: DS-1042 del seed 1.200 + TC-01 450 + NA-090 aprobada por el CFO 3.500 + DS-2026-1107 por la web 1.000)*
- [x] Tesorería real marcada en [roadmap.md](../roadmap.md).

## No bloqueantes

- Mostrar el presupuesto mensual y el gasto del mes (FIN-02) en el dashboard.
- Alinear el chat ilustrativo de "Telegram Live Demo" con la tesorería real.
