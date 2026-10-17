# Validación — Tesorería real en el dashboard

> La rama `fix/tesoreria-real` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código y del recorrido local.
> Criterio: el hero y la tarjeta de colchón muestran la misma tesorería y el mismo colchón con los que decide el agente.

## Criterios bloqueantes

### Código y pruebas

- [x] `pytest` en `backend/` verde, incluida `tests/test_treasury_api.py`. *(70 pasadas, 6 omitidas sin `TEST_DATABASE_URL`)*
- [x] `tests/test_postgres_integration.py` contra PostgreSQL 16 con seed: `/api/treasury` devuelve `balance_usd = 8500` y `monthly_budget_usd = 25000`. *(6 pasadas)*
- [x] `month_spent_usd` suma solo facturas aprobadas (`AUTO_APPROVED` y `HUMAN_APPROVED`) del mes en curso; una `REJECTED` no cuenta.
- [x] La prueba de arquitectura sigue en verde (el Core no importa FastAPI).
- [x] `npm run build` en `frontend/` sin errores.
- [x] Ningún componente conserva los valores fijos `$48,250`, `$10,000` ni `79%` en el hero o en la tarjeta de colchón. *(queda solo el chat ilustrativo de `AgentWorkflow.jsx`, fuera de alcance)*

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [x] El hero muestra "$8,500.00 USD", "Colchón protegido: $1,000 USD" y "Liquidez 88% OK"; el umbral autónomo muestra "$2,000".
- [x] La tarjeta "Colchón Mínimo Tesorería" muestra "Caja: $8,500 USD" y "Holgura 88% OK".
- [x] Al escribir 9000 en la reserva, sin guardar, la tarjeta muestra "Holgura 0% bajo el colchón" en rojo y la barra queda en 0.
- [x] Sin errores en la consola del navegador.
- [x] Sin modo demostración: los valores vienen de `GET /api/treasury` y `GET /api/rules`.

## Después del merge (producción)

- [ ] El dashboard público muestra la caja y el colchón de producción (hoy $8,500 y $1,000) en el hero y en la tarjeta.
- [ ] `GET https://backend-production-ea088.up.railway.app/api/treasury` responde `200`.
- [ ] Tesorería real marcada en [roadmap.md](../roadmap.md).

## No bloqueantes

- Mostrar el presupuesto mensual y el gasto del mes (FIN-02) en el dashboard.
- Alinear el chat ilustrativo de "Telegram Live Demo" con la tesorería real.
