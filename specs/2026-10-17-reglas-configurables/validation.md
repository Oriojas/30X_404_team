# Validación — Reglas configurables completas

> La rama `feat/reglas-configurables` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, de integración con PostgreSQL y del recorrido local en el navegador.
> Criterio: la empresa define desde el dashboard el tope por pago, el umbral de aprobación humana, el presupuesto del periodo y los beneficiarios permitidos con su tarifa, y la siguiente factura se decide con esas reglas. Ningún pago por encima del tope duro sale aprobado, ni por el agente ni por una persona.

## Criterios bloqueantes

### Código y pruebas (CI)

- [ ] `pytest` en `backend/` verde en el CI de F5.7, con las pruebas nuevas de la Fase 7 y las adaptadas de HITL-02.
- [ ] `PATCH /api/treasury` con solo `monthly_budget_usd` cambia el presupuesto y **no** mueve `snapshot_at` ni libera lo comprometido; con solo `balance_usd` sigue tomando la foto (Fase 6); con cuerpo vacío, `0`, negativo o texto (en cualquiera de los dos campos) responde `422`. `test_patch_ignora_el_presupuesto_hasta_la_fase_7` fue reemplazada, no borrada sin más. Con solo presupuesto y sin fila de tesorería responde `409` y no inserta nada (los dos fakes de tesorería y PostgreSQL).
- [ ] Las validaciones `422` que ya existían siguen igual: `test_patch_rechaza_saldo_invalido`, `duplicate_check_days` fuera de 1–365, umbral o colchón negativos, `decided_by` vacío y `Idempotency-Key` de más de 200 caracteres.
- [ ] Bajar el presupuesto hace que la siguiente factura, que antes salía `AUTO_APPROVED`, escale por FIN-02.
- [ ] Una factura por encima de `max_payment_usd` queda `REJECTED` por FIN-04, con el monto y el tope en la explicación; con INTEG-04 la Capa 3 queda `SKIPPED` y FIN-04 no aparece.
- [ ] `POST /api/rules` con `max_payment_usd` por debajo de `max_autonomous_usd` (también en una actualización parcial contra las reglas guardadas, y al subir el umbral por encima del tope) responde `422` con `detail[0].loc` terminando en el campo; las reglas no cambian.
- [ ] Aprobar desde el caso de uso una factura escalada cuyo monto supera un tope rebajado después responde `409` y la factura sigue `SCALED_TO_HUMAN`; rechazarla sí funciona. El docstring de `decide_invoice.py` ya no dice que la persona siempre puede aprobar.
- [ ] Subir la tarifa de un proveedor quita INTEG-02 de su siguiente factura (TC-07 deja de escalar con la tarifa en $1,500).
- [ ] `POST /api/vendors` crea un proveedor (`201`) con `active = true`, `is_pep = false`, `updated_by` y `updated_at` en UTC; con `tax_id` repetido o con una razón social que ya existe (aunque cambien las mayúsculas) responde `409`; sin `updated_by`, con textos vacíos o más largos que la columna, o con tarifa ≤ 0, `422` (nunca `500`).
- [ ] `PATCH /api/vendors/{id}` edita cuenta, tarifa, razón social y estado; con `tax_id` o `is_pep` en el cuerpo responde `422`; con id inexistente, `404`.
- [ ] Un proveedor dado de alta por la API: su siguiente factura ya no escala por HITL-02.
- [ ] Un proveedor dado de baja: su siguiente factura escala por HITL-02 ("inactivo") y sigue evaluando COMP-02 e INTEG-02 contra su registro.
- [ ] Un proveedor registrado y activo **sin historial de pagos** no escala por HITL-02, y si sale `AUTO_APPROVED` el Audit Log dice "proveedor activo en la lista permitida" (no "con historial"). `vendor_has_paid_history` y `vendor_has_history` ya no existen en el código.
- [ ] `main.py` tiene un handler por base (`NotFoundError` → `404`, `ConflictError` → `409`) más los de `503` y del `422` de reglas; las pruebas `404`/`409` que ya existían siguen en verde.
- [ ] TC-03 (proveedor no registrado) sigue escalando por HITL-02.
- [ ] `test_architecture.py` verde: los casos de uso nuevos solo usan puertos; los routers no importan adaptadores de salida.
- [ ] `npm run build` en `frontend/` sin errores.

### Integración con PostgreSQL 16 (local, Docker)

- [ ] `test_postgres_integration.py` verde con `TEST_DATABASE_URL`, con TC-01 a TC-08 dando lo esperado.
- [ ] `schema.sql` agrega `company_rules.max_payment_usd` (default $20,000), `vendors.active`, `vendors.updated_by` y `vendors.updated_at` sobre una base que ya tenía el esquema de la Fase 6; la fila de reglas existente toma el default.
- [ ] `schema.sql` y `seed.sql` siguen siendo idempotentes (`psql -v ON_ERROR_STOP=1`, dos veces cada uno).
- [ ] `PostgresVendorRepository.find` devuelve un proveedor inactivo con `active = false`.
- [ ] El índice `uq_vendors_legal_name` existe y un `INSERT` con la misma razón social en otras mayúsculas se traduce a `409`, no a `500`.
- [ ] TC-08 restaura el presupuesto original al terminar, también cuando el caso falla.

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [ ] `humo_produccion.py` contra el backend local: TC-01 a TC-08 dan el resultado esperado y el presupuesto queda como estaba; una segunda corrida seguida da lo mismo.
- [ ] El panel de reglas muestra y guarda el tope por pago y el presupuesto mensual; la tarjeta de presupuesto se actualiza sin recargar la página. En modo demostración el tope muestra $20,000 (`DEFAULT_RULES`), no un campo vacío.
- [ ] Un tope por debajo del umbral autónomo muestra el error `422` junto al campo (por `ApiError.fieldErrors`), no como mensaje general.
- [ ] Si el `PATCH` del presupuesto falla después de guardar las reglas, el panel muestra el error junto al presupuesto y los valores recargados de la API (D15).
- [ ] El panel de beneficiarios lista los seis proveedores del seed con cuenta, tarifa, PEP y estado.
- [ ] Alta de "Diseño Creativo Bogotá S.A.S." desde el panel: la siguiente factura suya (TC-03 con otro número) ya no escala por HITL-02. El panel muestra quién ("CFO Demo", de `DECIDED_BY`) y cuándo la dio de alta.
- [ ] Dar de baja a AWS desde el panel: una factura nueva de AWS escala por HITL-02 ("inactivo"); reactivarlo la deja `AUTO_APPROVED` otra vez.
- [ ] Un `tax_id` repetido en el formulario muestra el mensaje del `409`.
- [ ] Con la API caída: banner de demostración, proveedores del seed en el panel y formulario deshabilitado.
- [ ] Sin errores de JavaScript en la consola (salvo los `409`/`422` provocados a propósito).

## Después del merge (producción)

- [ ] Tras el deploy, `GET /api/rules` devuelve `max_payment_usd = 20000` y `GET /api/vendors` lista los proveedores del seed con `active = true` (la migración corrió con `DB_AUTO_MIGRATE=true`).
- [ ] `humo_produccion.py` verde contra producción con TC-08, y el presupuesto de producción queda igual que antes de la corrida.
- [ ] El dashboard público edita el tope y el presupuesto y muestra el panel de beneficiarios sin modo demostración; sin errores en la consola.
- [ ] F7.1 a F7.7 marcados en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## No bloqueante

- Autenticación y roles en los endpoints nuevos (Fase 8): hasta entonces cualquiera con la URL puede editar reglas y beneficiarios, igual que hoy con `POST /api/rules`.
- Historial de cambios de reglas y proveedores.
- Editar `is_pep` y `tax_id`.
