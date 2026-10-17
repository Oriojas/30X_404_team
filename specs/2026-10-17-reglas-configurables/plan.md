# Plan — Reglas configurables completas

> Rama: `feat/reglas-configurables`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).

## 0. Errores de dominio por tipo (backend, base de las fases siguientes)

0.1. `errors.py`: bases `NotFoundError(DomainError)` y `ConflictError(DomainError)`. `InvoiceNotFoundError` hereda de la primera; `InvalidDecisionStateError` y `UnconvertedAmountApprovalError`, de la segunda. Sin cambiar sus mensajes (D16).
0.2. `main.py`: un `exception_handler` por base (`404` y `409`) en lugar de uno por error; se conservan el de `DatabaseUnavailableError` (`503`) y el nuevo de `InvalidFieldError` (`422`, paso 2.3). Las pruebas actuales de `404`/`409` siguen en verde sin tocarlas.

## 1. Presupuesto del periodo (backend, F7.1)

1.1. `schemas.py`: `TreasuryBalanceUpdate` (mismo nombre) con `balance_usd` y `monthly_budget_usd` opcionales (`Field(gt=0)`) y un `model_validator` que exige al menos uno, para que `{}` siga en `422` como hoy (D1).
1.2. Puerto `TreasuryRepository`:
   - `set_balance(company_id, balance_usd, as_of, monthly_budget_usd=None)`: el upsert de la Fase 6 en **una** sentencia. Si llega presupuesto, también lo escribe; si no, conserva el guardado (en el `INSERT` usa el default) (D2).
   - `set_monthly_budget(company_id, monthly_budget_usd)` nuevo: **solo `UPDATE`**, sin tocar `updated_at` ni `balance_usd`. Si no hay fila, lanza `TreasuryNotInitializedError(ConflictError)` (`409`: "registra primero el saldo con `balance_usd`"). Nunca inserta: un `INSERT` crearía un saldo inventado y una foto nueva (D2).
1.3. `UpdateTreasuryBalanceUseCase` (mismo nombre) gana el parámetro opcional `monthly_budget_usd`. Con saldo, llama a `set_balance` con ambos campos; con solo presupuesto, llama a `set_monthly_budget`. Todo bajo el `asyncio.Lock` de F6.4. No cambian `container.py`, `dependencies.py` ni `use_cases/__init__.py`.
1.4. Router `treasury.py`: pasar los dos campos al caso de uso.
1.5. `tests/fakes.py`: `FixedTreasury` y `LedgerTreasury` guardan `monthly_budget_usd` en un atributo (hoy los dos lo fijan en `25000` dentro de `get()`), lo devuelven en `get()` e implementan `set_monthly_budget` sin mover la foto. `set_balance` de ambos acepta el presupuesto opcional.
1.6. `test_treasury_api.py`: reemplazar `test_patch_ignora_el_presupuesto_hasta_la_fase_7` por `test_patch_con_presupuesto_no_mueve_la_foto`; ampliar `test_patch_rechaza_saldo_invalido` con `{"monthly_budget_usd": 0}`, `-1` y texto; `409` con solo presupuesto y sin fila de tesorería.

## 2. Tope duro por pago (Core, F7.2)

2.1. `schema.sql`: `ALTER TABLE company_rules ADD COLUMN IF NOT EXISTS max_payment_usd NUMERIC(12,2) DEFAULT 20000.00` (D3, D12). `CompanyRules.max_payment_usd: float = 20000.00`; lectura y escritura en `PostgresRulesRepository`.
2.2. `CompanyRulesUpdate` y `CompanyRulesResponse` con `max_payment_usd` (`ge=0`).
2.3. `UpdateRulesUseCase`: combinar la actualización con las reglas guardadas (sin cambiar el filtro `hasattr` actual) y, si `max_payment_usd < max_autonomous_usd`, lanzar `InvalidFieldError(field, message)` (`errors.py`). Su handler en `main.py` responde `422` con `{"detail": [{"loc": ["body", field], "msg": message}]}` (D4).
2.4. `tests/fakes.py`: `InMemoryRules` guarda `self.current` (inicializado con los overrides): `save` lo reemplaza y `get` lo devuelve. Así una regla guardada afecta la siguiente factura. No se crea otro fake de reglas.
2.5. `_solvency` en `rules_pipeline.py`: FIN-04 `REJECTED` si `ctx.usd_amount > rules.max_payment_usd`, con el monto y el tope en la explicación. Sin guarda de `currency_supported`: `evaluate_invoice` ya marca toda la Capa 3 como `SKIPPED` cuando no hay conversión a USD.
2.6. `DecideInvoiceUseCase`: si la revalidación de la Capa 3 trae FIN-04, lanzar `PaymentCapExceededError(ConflictError)` → `409` (D5). Actualizar el docstring del módulo: deja de ser cierto que "la persona siempre puede aprobar" (excepciones: INTEG-04 y FIN-04).
2.7. Documentar FIN-04 en [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md).

## 3. Beneficiarios permitidos (backend, F7.3)

3.1. `schema.sql`: `vendors.active BOOLEAN DEFAULT TRUE`, `vendors.updated_by VARCHAR(100)`, `vendors.updated_at TIMESTAMP`, la función `vendor_key(text)` (`CREATE OR REPLACE`, `IMMUTABLE`) y los índices únicos `uq_vendors_tax_id_key` y `uq_vendors_legal_name_key` sobre `vendor_key(...)`, todo idempotente (D12, D17).
3.2. `Vendor` en `models.py`: `id`, `active`, `updated_by`, `updated_at` (D10).
3.3. Puerto `VendorRepository`: `list_all()`, `get(id)`, `create(vendor)` y `update(vendor)`. Un NIT o una razón social repetidos, aun con otro formato, lanzan `VendorAlreadyExistsError(ConflictError)` (el adaptador traduce `UniqueViolationError` por el nombre del índice); un id inexistente, `VendorNotFoundError(NotFoundError)`. `find` sigue devolviendo inactivos (D8). `InMemoryVendors` implementa lo mismo con `_normalize`.
3.4. Caso de uso `manage_vendors.py`: `ListVendorsUseCase`, `CreateVendorUseCase` y `UpdateVendorUseCase`, con `updated_at` del reloj de la app (UTC, D9) y solo los campos editables de D7.
3.5. Router `vendors.py` (`GET`, `POST` → `201`, `PATCH /{id}`) con `VendorCreate`, `VendorUpdate` (`extra="forbid"`) y `VendorResponse` (fechas UTC con `Z`, como F5.8), con los límites de D14. Los `404`/`409` salen de los handlers por base del paso 0.2. Registrar el router en `main.py`.
3.6. `backend/README.md`: endpoints de beneficiarios y el `PATCH /api/treasury` ampliado.
3.7. `find` empata por `vendor_key(tax_id)` y, si no, por `vendor_key(legal_name)` no vacía, prefiriendo el NIT (D17). Prompt de Gemini (`gemini_ocr.py`, regla 6): `vendor_tax_id` sin la etiqueta. Pruebas: formatos distintos de NIT y razón social encuentran al proveedor (fake y PostgreSQL), alta duplicada con otro formato → `409`, y `vendor_key` de PostgreSQL igual a `_normalize` en ejemplos con tildes, puntos y guiones.
3.8. COMP-01: `find_match` de sanciones compara razón social, NIT y cuenta con `vendor_key`, sin llaves vacías (D18).

## 4. HITL-02 como lista permitida (Core, F7.4)

4.1. `_hitl`: HITL-02 si `ctx.vendor is None` ("Beneficiario fuera de la lista permitida…") o `not ctx.vendor.active` ("Beneficiario inactivo en la lista permitida…") (D6).
4.2. `_explain`: el texto de `AUTO_APPROVED` cambia "proveedor verificado con historial" por "proveedor activo en la lista permitida". Si no, un proveedor recién dado de alta, sin pagos, sale aprobado con una justificación falsa.
4.3. Borrar `EvaluationContext.vendor_has_history`, `vendor_has_paid_history` (puerto, adaptador PostgreSQL y fake) y la llamada en `process_invoice.py`.
4.4. `seed.sql`: corregir el comentario del historial (sigue sirviendo a TC-02 y a FIN-02, ya no a HITL-02).
4.5. Adaptar `test_rules_pipeline.py`, `test_process_invoice.py` y `test_ingestion_idempotency.py`, y las aserciones sobre el texto de `AUTO_APPROVED`.
4.6. Documentar el cambio de HITL-02 en [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md).

## 5. Panel en el dashboard (frontend, F7.5)

5.1. `api.js`: `max_payment_usd: 20000` en `DEFAULT_RULES` (el mismo default del backend), para que el input no quede `undefined` en modo demostración ni antes de que llegue `GET /api/rules`.
5.2. `api.js`: `getVendors`, `createVendor`, `updateVendor` y `updateTreasury({balance_usd?, monthly_budget_usd?})`, con los errores `422` por campo y `409` como en `saveRules`. `createVendor` y `updateVendor` envían `updated_by: DECIDED_BY`, igual que `decideInvoice`: una sola convención de autor hasta la Fase 8. Proveedores del seed como respaldo de demostración (D13).
5.3. `RuleControls.jsx`: campos numéricos de tope por pago (`max_payment_usd`, por `POST /api/rules`) y de presupuesto mensual (por `PATCH /api/treasury`), agregados a `RULE_FIELDS` para que su `422` salga junto al campo con `FieldError`. El slider del umbral autónomo ($500–$10,000) no cambia. Guardado en dos llamadas según D15; tras guardar, recargar reglas y tesorería.
5.4. `VendorsPanel.jsx` nuevo: tabla con razón social, NIT, cuenta, tarifa, PEP (solo lectura), estado y último cambio (`updated_by` y fecha); formulario de alta y edición; botón activar/desactivar. Sin campo de autor: lo pone `api.js`.
5.5. Montar el panel en el dashboard junto a las reglas; tokens de [DESIGN.md](../../docs/diseno/DESIGN.md).

## 6. Caso trampa TC-08 (F7.6)

6.1. `casos_demo.py`: agregar TC-08 (`SCALED_TO_HUMAN`, FIN-02) con la factura de AWS por $400 y una función que calcula el presupuesto de prueba a partir de `GET /api/treasury` (D11).
6.2. `humo_produccion.py`: antes de TC-08, `PATCH` del presupuesto a `gasto del mes + 400 − 1`; después, restaurar el original en un `finally`.
6.3. `test_postgres_integration.py`: el mismo flujo con PostgreSQL.
6.4. Test Suite en [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md) y [mission.md](../mission.md): TC-08 y "los ocho casos".

## 7. Pruebas y cierre (F7.7)

7.1. Unitarias del pipeline: FIN-04 `REJECTED` por encima del tope y Capa 3 `SKIPPED` con INTEG-04; HITL-02 por proveedor no registrado, por inactivo y ausente para un proveedor activo sin historial; un inactivo conserva COMP-02 e INTEG-02; el texto de `AUTO_APPROVED` ya no menciona historial.
7.2. Casos de uso: un cambio de presupuesto, tope o tarifa cambia la decisión de la siguiente factura; un proveedor dado de alta deja de escalar por HITL-02; uno dado de baja vuelve a escalar; el `PATCH` con solo presupuesto no mueve `snapshot_at` (en los dos fakes de tesorería); aprobar por encima de un tope rebajado → `409`.
7.3. API: `422` (presupuesto ≤ 0, cuerpo vacío, tope < umbral con `loc` del campo, umbral subido sobre el tope, `updated_by` vacío o > 100, textos más largos que la columna, `tax_id`/`is_pep` en el `PATCH`); `409` por NIT o razón social repetidos (también con otro formato: puntos, guiones, tildes o mayúsculas) y por presupuesto sin fila de tesorería; `404` por id inexistente. Las pruebas `404`/`409`/`422` actuales siguen en verde.
7.4. `test_postgres_integration.py`: columnas nuevas, índice único de razón social, `find` con inactivos, `set_monthly_budget` sin fila no inserta nada, TC-01 a TC-08.
7.5. `pytest` y `npm run build`; integración con PostgreSQL 16 en Docker (`TEST_DATABASE_URL`); `schema.sql` y `seed.sql` dos veces.
7.6. Recorrido en el navegador con backend local y seed (checklist de [validation.md](validation.md)).
7.7. Tras el merge: verificación en producción y marcar F7.1 a F7.7 en el roadmap con la evidencia.
