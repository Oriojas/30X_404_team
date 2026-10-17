# Validación — Tesorería comprometida

> La rama `feat/tesoreria-comprometida` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, de integración con PostgreSQL y del recorrido local en el navegador.
> Criterio: el agente nunca aprueba solo un pago que deje lo comprometido por encima del saldo o del presupuesto, ni siquiera con ingestas simultáneas, y cada pago que una persona aprueba fuera de esos límites queda registrado como excepción aprobada por ella.

## Criterios bloqueantes

### Código y pruebas (CI)

- [x] `pytest` en `backend/` verde en el CI de F5.7, con las pruebas nuevas de la Fase 6. *(CI del PR en verde. En local, tras la revisión de código: 88 pasadas y 7 omitidas sin `TEST_DATABASE_URL`.)*
- [x] Cinco facturas de $1,900 (proveedor con historial, dentro de tarifa y umbral) con $8,500 de saldo y $1,000 de colchón: las tres primeras `AUTO_APPROVED` (disponible $2,800) y la cuarta y la quinta escalan por FIN-03 ($2,800 − $1,900 queda bajo el colchón); lo comprometido nunca supera el saldo. *(`test_cinco_facturas_que_caben_solas_pero_no_juntas`, con Nube Andina: la tarifa de $1,000 de AWS dispararía INTEG-02.)*
- [x] El historial del seed anterior a la foto no compromete nada: TC-01 sale `AUTO_APPROVED`. *(integración: `committed_usd = 0` tras el seed)*
- [x] La explicación de FIN-01 y FIN-03 cita saldo de la foto, comprometido y disponible. *(`test_fin01_...` y `test_fin03_...` en `test_rules_pipeline.py`)*
- [x] Aprobar TC-05 desde el caso de uso deja `HUMAN_APPROVED` y el Audit Log registra el disponible y las alertas FIN vigentes como excepción aprobada por esa persona. *(`test_aprobar_revalida_la_solvencia_y_registra_la_excepcion`: "disponible $7,000.00 USD", `[FIN-01]` y "Excepción aprobada por CFO Blinka")*
- [x] Aprobar una factura INTEG-04 (`usd_amount = 0`) responde `409` y la factura sigue en `SCALED_TO_HUMAN`; rechazarla sí funciona. *(unitaria y, con el `409`, en la integración)*
- [x] Dos ingestas concurrentes de $4,000 con $8,500 de saldo y $1,000 de colchón: exactamente una `AUTO_APPROVED`. *(`test_dos_ingestas_concurrentes_...` usa $4,000 y $4,100 para que INTEG-01 no las tome como duplicadas; la otra escala por FIN-03. Sin el candado, la prueba falla.)*
- [x] `PATCH /api/treasury` con `balance_usd` válido devuelve la tesorería con `committed_usd = 0` y `snapshot_at` nuevo; con `0`, negativo o sin campo responde `422`; con `monthly_budget_usd` en el cuerpo no cambia el presupuesto. *(`test_treasury_api.py`)*
- [x] Las pruebas que construían `DecideInvoiceUseCase(invoices, notifier)` están adaptadas; la prueba de arquitectura sigue en verde (el candado es `asyncio.Lock` de la librería estándar; el Core no importa FastAPI ni adaptadores). *(`test_architecture.py` verde)*
- [x] `npm run build` en `frontend/` sin errores.

### Integración con PostgreSQL 16 (local, Docker)

- [x] `test_postgres_integration.py` verde con `TEST_DATABASE_URL`. *(7 pasadas con PostgreSQL 16 en Docker y `timezone=America/Bogota`; 95 en total tras la revisión de código)*
- [x] Lo comprometido suma `AUTO_APPROVED` por `processed_at` y `HUMAN_APPROVED` por `decided_at`, solo después de `updated_at`. *(`test_tesoreria_compromete_lo_aprobado_despues_de_la_foto_...`: comprometido $900 de $2,800 aprobados)*
- [x] FIN-02 cuenta un `HUMAN_APPROVED` en el mes de su `decided_at`, no en el de su `processed_at`. *(misma prueba: ingresada hace 40 días y aprobada hoy cuenta; ingresada hoy y aprobada hace 40 días no)*
- [x] `updated_at` queda en UTC tras `schema.sql`, `seed.sql` y el `PATCH` (sin desfase de la zona del servidor). *(base en `America/Bogota`. El `PATCH` usa el reloj de la app, ver D3: con `now()` de la base, que iba unos 20 ms detrás, una aprobación hecha justo antes quedaba después de la foto.)*
- [x] `schema.sql` y `seed.sql` siguen siendo idempotentes (se pueden correr dos veces). *(`psql -v ON_ERROR_STOP=1`, dos veces cada uno)*

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [x] `humo_produccion.py` toma una foto nueva (con `SALDO_DEMO_USD` de `casos_demo.py`) y TC-01 a TC-07 dan el resultado esperado; una segunda corrida seguida da lo mismo. *(Local: 11/11 y luego 10/10. Antes del humo se aprobó una factura de $7,777, que dejó el disponible en $723: sin la foto, una factura normal de $1,234 escalaba por FIN-01.)*
- [x] El hero muestra el disponible, el saldo de la foto y lo comprometido de `GET /api/treasury`. *("$8,050.00 USD" con saldo $8,500 y comprometido $450 tras TC-01; "Liquidez 88% OK")*
- [x] Tras una aprobación desde el Drawer, el hero baja el disponible sin recargar la página. *(TC-05: comprometido $450 → $10,450 y disponible "-$1,950.00 USD", liquidez "0% bajo el colchón")*
- [x] Tras subir una factura que sale `AUTO_APPROVED`, el hero baja el disponible. *(Local con Gemini real: `factura_devstudio.png` → `AUTO_APPROVED` DS-2026-1107 por $1,000; `POST /upload` 201 seguido de `GET /api/treasury`, y el hero pasa de $8,500 a $7,500 disponible con $1,000 comprometido, sin recargar la página)*
- [x] La tarjeta de presupuesto muestra presupuesto mensual, gasto del mes y restante, y coincide con la respuesta del endpoint. *($25,000, $11,650 y $13,350 tras aprobar TC-05)*
- [x] Aprobar TC-05 desde el Drawer muestra en el Audit Log la excepción con el disponible. *("Excepción aprobada por CFO Demo con alertas FIN vigentes: [FIN-01] …")*
- [x] Aprobar una factura INTEG-04 desde el Drawer muestra el mensaje del `409` y la factura sigue escalada. *(AWS-GBP-1)*
- [x] Con la API caída: banner de demostración y valores del seed ($8,500 disponible, $0 comprometido, liquidez 88 % OK, presupuesto $25,000).
- [x] Con la API viva pero `GET /api/treasury` fallando, el hero y las tarjetas muestran "—". *(Local: con `treasury_accounts` renombrada, `/api/treasury` responde 500 y health, invoices y rules 200. Hero, colchón y presupuesto muestran "—" sin banner de demostración; al restaurar la tabla vuelve el disponible de $7,500.)*
- [x] Sin errores de JavaScript en la consola. *(solo el `409` esperado de la factura INTEG-04)*

## Después del merge (producción)

- [x] Justo después del deploy, `PATCH /api/treasury` con el saldo del seed (o `humo_produccion.py`): la fila existente conserva el `updated_at` del seed original y, sin la foto, todo lo aprobado desde entonces compromete el saldo (ver `backend/README.md`). *(17-oct-2026, tras el merge de #20. Antes de la foto, producción tenía $7,950 comprometidos y $550 disponibles (foto de las 10:00 UTC). Después: comprometido $0, disponible $8,500, foto de las 15:48 UTC.)*
- [x] `humo_produccion.py` verde contra producción, con la foto tomada antes de TC-01. *(11/11, con CORS. Los 7 casos respondieron `200`: son la repetición de corridas anteriores (misma `Idempotency-Key`), no una evaluación nueva del deploy. La lógica nueva quedó evaluada en local y en la integración con PostgreSQL.)*
- [x] El dashboard público muestra el disponible y el presupuesto del mismo `GET /api/treasury` con que decide el agente. *(Sin modo demostración: disponible $8,500.00, saldo $8,500.00, comprometido $0.00, liquidez 88 % OK; presupuesto $25,000, gasto del mes $9,150, restante $15,850. Sin errores en la consola.)*
- [x] F6.1 a F6.6 marcados en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## No bloqueante

- Variante estricta de la revalidación (F9.7) y prueba de aprobaciones concurrentes (F9.8).
- Varias réplicas (`pg_advisory_xact_lock`).
