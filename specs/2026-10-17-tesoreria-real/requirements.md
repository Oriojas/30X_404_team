# Requisitos — Tesorería real en el dashboard

> Rama: `fix/tesoreria-real` · Complemento de la Fase 4 de [roadmap.md](../roadmap.md) (T1 a T3).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

Al validar la Fase 4 en producción, el dashboard mostraba valores de tesorería que no salían del backend:

- El hero tenía fijos "Tesorería Operativa Disponible: $48,250.00 USD", "Colchón protegido: $10,000 USD", "Liquidez 79% OK" y el umbral autónomo "$2,000".
- La tarjeta "Colchón Mínimo Tesorería" tenía fijos "Caja: $48,250 USD" y "Holgura 79% OK", aunque su campo de reserva sí venía de `GET /api/rules`.
- `DEFAULT_RULES.min_treasury_buffer_usd` en `frontend/src/api.js` valía `10000`. El valor por defecto real del backend es `1000` (modelo `CompanyRules`, `schema.sql` y `seed.sql`), y producción tiene `1000`. Nadie lo cambió a mano: el `10000` venía del diseño de prueba de la landing.
- El saldo real del seed es $8,500 USD (TC-05 lo supera), pero no existía ningún endpoint para leerlo: la tesorería solo la usaba la tubería (FIN-01, FIN-02, FIN-03).

Mostrar al jurado $48,250 de caja y $10,000 de colchón mientras el agente decide con $8,500 y $1,000 contradice el principio de explicabilidad: el dashboard debe reflejar lo que el agente usa para decidir.

## Alcance

**Entra:**
- `GET /api/treasury` (solo lectura) con saldo, presupuesto mensual y gasto aprobado del mes de la cuenta Blinka.
- `DEFAULT_RULES.min_treasury_buffer_usd = 1000` en el frontend.
- Hero: caja, colchón, umbral autónomo y liquidez con los valores reales.
- Tarjeta "Colchón Mínimo Tesorería": caja y holgura reales; la holgura se recalcula mientras se edita la reserva.
- Pruebas del endpoint (unitaria e integración con PostgreSQL) y `backend/README.md`.

**No entra:**
- Editar el saldo o el presupuesto desde el dashboard (la tesorería real es V3 de la visión).
- Mostrar el presupuesto mensual o el gasto del mes en la UI: el endpoint los devuelve, pero ningún componente los usa todavía.
- El chat ilustrativo de "Telegram Live Demo" (`AgentWorkflow.jsx`), que sigue diciendo "Saldo Bóveda OK ($48,250 USD)".
- Refresco automático de la tesorería: se lee al abrir la página.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **Endpoint propio y de solo lectura:** `GET /api/treasury` devuelve `{balance_usd, monthly_budget_usd, month_spent_usd}` mediante `GetTreasuryUseCase`, que solo delega en `TreasuryRepository.get`. El router usa `TreasuryResponse.from_domain`, como el resto de los esquemas. | Respeta la arquitectura hexagonal (el router recibe un caso de uso, nunca el contenedor) y no mezcla tesorería con las reglas. |
| D2 | **El repositorio de tesorería trae el gasto del mes:** `PostgresTreasuryRepository.get` devuelve saldo, presupuesto y acumulado aprobado (`AUTO_APPROVED` y `HUMAN_APPROVED`) desde el 1.º del mes en UTC, en una sola consulta. `InvoiceRepository.sum_approved_usd_since` desaparece. La tubería y el endpoint usan el mismo `get`. `invoices` no tiene `company_id` (MVP de una empresa), así que el acumulado es de toda la tabla. | Una sola fuente para FIN-02: el dashboard muestra exactamente lo que usa la tubería, sin duplicar el armado ni hacer dos consultas seguidas. |
| D3 | **Holgura = (saldo − colchón) / saldo**, acotada entre 0 % y 100 %, en `treasuryHeadroom()` de `api.js`. "OK" (verde) si el saldo supera el colchón; si no, "bajo el colchón" (rojo). Por encima del colchón con menos de medio punto se muestra "<1% OK", nunca "0% OK". Si falta el saldo o la reserva no es un número válido (campo vacío), se muestra "—". | Es la misma fórmula que daba el 79 % del diseño original ($48,250 y $10,000), ahora con datos reales. FIN-03 escala cuando el saldo menos el pago cae bajo el colchón. |
| D4 | **Seed solo en modo demostración:** `DEFAULT_TREASURY = {8500, 25000, 0}` se muestra únicamente cuando la API no responde (con el banner de demostración). Si la API responde pero `GET /api/treasury` falla (por ejemplo, un backend anterior sin el endpoint), el hero y la tarjeta muestran "—". | Con la API viva nunca se muestra un saldo inventado como si fuera real (misma regla que D1 de la Fase 3). |
| D5 | **La holgura de la tarjeta sigue al campo editado**, no a la regla guardada; el hero usa la regla guardada. | El operador ve el efecto de una reserva antes de guardarla, y el hero siempre muestra lo vigente. |
| D6 | **Sin dependencias nuevas** ni variables de entorno nuevas. | Pragmatismo de hackathon. |

## Contrato de la API

| Endpoint | Uso | Respuesta |
| :--- | :--- | :--- |
| `GET /api/treasury` | Hero y tarjeta de colchón | `200` con `{"balance_usd": 8500.0, "monthly_budget_usd": 25000.0, "month_spent_usd": 1200.0}` |
| `GET /api/rules` | Colchón y umbral autónomo (sin cambios) | `200` con `min_treasury_buffer_usd` y `max_autonomous_usd` |

## Restricciones

- El Core no importa frameworks (lo verifica `tests/test_architecture.py`).
- Textos de la UI en español.
- `npm run build` sin errores y `pytest` en verde.
