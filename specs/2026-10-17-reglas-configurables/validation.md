# Validación — Reglas configurables completas

> La rama `feat/reglas-configurables` se puede mergear cuando se cumplen **todos** los criterios bloqueantes de código, de integración con PostgreSQL y del recorrido local en el navegador.
> Criterio: la empresa define desde el dashboard el tope por pago, el umbral de aprobación humana, el presupuesto del periodo y los beneficiarios permitidos con su tarifa, y la siguiente factura se decide con esas reglas. Ningún pago por encima del tope duro sale aprobado, ni por el agente ni por una persona.

## Criterios bloqueantes

### Código y pruebas (CI)

- [ ] `pytest` en `backend/` verde en el CI de F5.7, con las pruebas nuevas de la Fase 7 y las adaptadas de HITL-02.
- [x] `PATCH /api/treasury` con solo `monthly_budget_usd` cambia el presupuesto y **no** mueve `snapshot_at` ni libera lo comprometido; con solo `balance_usd` sigue tomando la foto (Fase 6); con cuerpo vacío, `0`, negativo o texto (en cualquiera de los dos campos) responde `422`. `test_patch_ignora_el_presupuesto_hasta_la_fase_7` fue reemplazada, no borrada sin más. Con solo presupuesto y sin fila de tesorería responde `409` y no inserta nada (los dos fakes de tesorería y PostgreSQL). *(`test_treasury_api.py`: `test_patch_con_presupuesto_no_mueve_la_foto` reemplaza a la prueba de la Fase 6; `test_patch_rechaza_saldo_o_presupuesto_invalido` con 8 cuerpos; `409` sin fila en el fake y en PostgreSQL: `test_presupuesto_solo_update_sin_mover_la_foto_ni_crear_la_fila`)*
- [x] Las validaciones `422` que ya existían siguen igual: `test_patch_rechaza_saldo_invalido`, `duplicate_check_days` fuera de 1–365, umbral o colchón negativos, `decided_by` vacío y `Idempotency-Key` de más de 200 caracteres. *(no tenían prueba propia; ahora la tienen: `test_validaciones_previas_de_reglas_siguen_en_422`, `test_decision_sin_autor_valido_es_422_antes_del_caso_de_uso`, más las de `test_treasury_api.py` y `test_api_idempotency.py`)*
- [x] Bajar el presupuesto hace que la siguiente factura, que antes salía `AUTO_APPROVED`, escale por FIN-02. *(`test_bajar_el_presupuesto_hace_escalar_por_fin02_la_siguiente_factura`; y TC-08 en la integración)*
- [x] Una factura por encima de `max_payment_usd` queda `REJECTED` por FIN-04, con el monto y el tope en la explicación; con INTEG-04 la Capa 3 queda `SKIPPED` y FIN-04 no aparece. *(`test_fin04_rechaza_por_encima_del_tope_duro_y_corta_la_capa_4`, `test_fin04_no_dispara_en_el_tope_exacto`, `test_fin04_no_se_evalua_sin_conversion_a_usd`)*
- [x] `POST /api/rules` con `max_payment_usd` por debajo de `max_autonomous_usd` (también en una actualización parcial contra las reglas guardadas, y al subir el umbral por encima del tope) responde `422` con `detail[0].loc` terminando en el campo; las reglas no cambian. *(`test_rules_api.py` contra la app de `main.py`: tres casos con `loc` del campo, la validación contra lo guardado en el caso de uso y, con el cuerpo completo que envía el dashboard, el error en el campo que cambió (`test_con_el_cuerpo_completo_del_dashboard_el_error_va_al_campo_que_cambio`); en PostgreSQL, `422` con un tope de $4,000 bajo un umbral de $5,000)*
- [x] Aprobar desde el caso de uso una factura escalada cuyo monto supera un tope rebajado después responde `409` y la factura sigue `SCALED_TO_HUMAN`; rechazarla sí funciona. El docstring de `decide_invoice.py` ya no dice que la persona siempre puede aprobar. *(`test_aprobar_por_encima_de_un_tope_rebajado_responde_conflicto_y_rechazar_si_funciona`; docstring actualizado)*
- [x] Subir la tarifa de un proveedor quita INTEG-02 de su siguiente factura (TC-07 deja de escalar con la tarifa en $1,500). *(`test_subir_la_tarifa_acordada_quita_integ02_de_la_siguiente_factura`, con DevStudio: tarifa $300 → INTEG-02, tarifa $400 → `AUTO_APPROVED`. Mismo mecanismo que TC-07, sin cambiar el seed)*
- [x] `POST /api/vendors` crea un proveedor (`201`) con `active = true`, `is_pep = false`, `updated_by` y `updated_at` en UTC; con un NIT o una razón social que ya existen, aun con otro formato (`900584112-4`, `Devstudio Latam SAS`), responde `409`; sin `updated_by`, con textos vacíos o más largos que la columna, o con tarifa ≤ 0, `422` (nunca `500`). *(`test_vendors_api.py`: alta, 409 por NIT y razón social con otro formato, 12 cuerpos inválidos en `422`; en PostgreSQL, `409` y nunca `500`)*
- [x] `PATCH /api/vendors/{id}` edita cuenta, tarifa, razón social y estado; con `tax_id` o `is_pep` en el cuerpo responde `422`; con id inexistente, `404`. *(`test_vendors_api.py`: edición, baja y reactivación, tarifa `null`, 7 cuerpos en `422`, `404`)*
- [x] Un proveedor dado de alta por la API: su siguiente factura ya no escala por HITL-02. *(`test_vendor_outside_the_allowlist_is_scaled_then_registered_vendor_is_approved_and_duplicate_rejected`)*
- [x] Un proveedor dado de baja: su siguiente factura escala por HITL-02 ("inactivo") y sigue evaluando COMP-02 e INTEG-02 contra su registro. *(`test_hitl02_proveedor_inactivo_escala_y_conserva_comp02_e_integ02`, `test_baja_logica_hace_escalar_la_siguiente_factura_y_reactivar_la_aprueba`)*
- [x] Un proveedor registrado y activo **sin historial de pagos** no escala por HITL-02, y si sale `AUTO_APPROVED` el Audit Log dice "proveedor activo en la lista permitida" (no "con historial"). `vendor_has_paid_history` y `vendor_has_history` ya no existen en el código. *(`test_hitl02_proveedor_activo_sin_historial_no_escala`; `grep` de `vendor_has_history` y `vendor_has_paid_history` vacío)*
- [x] `main.py` tiene un handler por base (`NotFoundError` → `404`, `ConflictError` → `409`) más los de `503` y del `422` de reglas; las pruebas `404`/`409` que ya existían siguen en verde. *(`test_error_handlers.py` contra la app de `main.py`)*
- [x] TC-03 (proveedor no registrado) sigue escalando por HITL-02. *(`test_tc03_new_vendor_is_scaled` y TC-03 en la integración y en el humo)*
- [x] `test_architecture.py` verde: los casos de uso nuevos solo usan puertos; los routers no importan adaptadores de salida. *(8 pasadas)*
- [x] `npm run build` en `frontend/` sin errores. *(build limpio con `VendorsPanel.jsx`)*

### Integración con PostgreSQL 16 (local, Docker)

- [x] `test_postgres_integration.py` verde con `TEST_DATABASE_URL`, con TC-01 a TC-08 dando lo esperado. *(11 pasadas; 173 en total con PostgreSQL 16 en Docker y la base en `America/Bogota`; 162 pasadas y 11 omitidas sin base)*
- [x] `schema.sql` agrega `company_rules.max_payment_usd` (default $20,000), `vendors.active`, `vendors.updated_by` y `vendors.updated_at` sobre una base que ya tenía el esquema de la Fase 6; la fila de reglas existente toma el default. *(base nueva con `schema.sql` y `seed.sql` de `master` (8bc5982) y luego los de la rama: 6 proveedores con `active = true` y `max_payment_usd = 20000.00` en la fila existente)*
- [x] `schema.sql` y `seed.sql` siguen siendo idempotentes (`psql -v ON_ERROR_STOP=1`, dos veces cada uno). *(dos veces cada uno sobre esa base, sin errores)*
- [x] `PostgresVendorRepository.find` devuelve un proveedor inactivo con `active = false`. *(`test_lista_permitida_con_el_seed_alta_unicidad_y_baja_logica`)*
- [x] Los índices `uq_vendors_tax_id_key` y `uq_vendors_legal_name_key` existen tras migrar una base con el esquema de `master`, y un `INSERT` con el mismo NIT o razón social en otro formato se traduce a `409`, no a `500`. *(presentes tras migrar desde `master`; `409` por API en la integración)*
- [x] `vendor_key` de PostgreSQL devuelve lo mismo que `_normalize` del Core para textos con tildes, `ñ`, puntos, guiones y espacios. *(`test_vendor_key_de_postgres_coincide_con_normalize_y_find_tolera_formatos`)*
- [x] COMP-01 (D18): `find_match` rechaza a Global Trade Partners con `PA1557788`, `global trade partners ltd.` y la cuenta con espacios; una llave vacía no empata. *(`test_find_match_de_sanciones_tolera_el_formato_del_ocr`; TC-06 sigue `REJECTED` por COMP-01 en la integración y en el humo)*
- [x] `vendor_key` no depende del locale: en una base con `LC_CTYPE=C`, `LOGÍSTICA ÑANDÚ` da `logisticanandu`, igual que `_normalize`. *(comprobado a mano en una base `C`; la integración agrega el ejemplo en mayúsculas)*
- [x] `find` encuentra a los proveedores del seed con formatos que puede devolver el OCR: `900584112-4`, `lem850101ab1`, `Logistica Express MX SA de CV`, `NUBE ANDINA CONSULTORES SAS`; el NIT manda sobre el nombre, y un nombre vacío o de solo signos no empata. *(misma prueba, con los cuatro formatos, el NIT sobre el nombre, y `...`, `None`, `-` y `N/A.` sin empate)*
- [x] TC-08 restaura el presupuesto original al terminar, también cuando el caso falla. *(integración: restaura y vuelve a $25,000 sin mover la foto. El caso con falla se cubre por construcción: `humo_produccion.py` restaura en un `finally`; no se provocó una falla real)*

### Recorrido local (backend + PostgreSQL con seed + `npm run dev`)

- [x] `humo_produccion.py` contra el backend local: TC-01 a TC-08 dan el resultado esperado y el presupuesto queda como estaba; una segunda corrida seguida da lo mismo. *(base recién sembrada: 12/12 y luego 12/12 con los 8 casos en `200`; presupuesto en $25,000 tras ambas corridas)*
- [x] El panel de reglas muestra y guarda el tope por pago y el presupuesto mensual; la tarjeta de presupuesto se actualiza sin recargar la página. En modo demostración el tope muestra $20,000 (`DEFAULT_RULES`), no un campo vacío. *(tope $18,000 y presupuesto $20,000 guardados; la tarjeta pasó a "Restante: $18,000 USD" sin recargar y el `GET` lo confirmó; en modo demostración el tope muestra 20000)*
- [x] Un tope por debajo del umbral autónomo muestra el error `422` junto al campo (por `ApiError.fieldErrors`), no como mensaje general. *(tope $1,500: mensaje bajo el campo con borde rojo y ningún aviso general)*
- [x] Si el `PATCH` del presupuesto falla después de guardar las reglas, el panel avisa que las reglas sí se guardaron, muestra el error junto al presupuesto y conserva el valor escrito para corregirlo (D15). *(ventana de 45 días y presupuesto 0: la ventana quedó guardada en la API, el aviso de guardado parcial y el `422` junto al presupuesto; corregido a $25,000 se guardó sin errores)*
- [x] El panel de beneficiarios lista los seis proveedores del seed con cuenta, tarifa, PEP y estado. *(6 filas con cuenta, tarifa, PEP de Consultora Riesgo Político y estado)*
- [x] Alta de "Diseño Creativo Bogotá S.A.S." desde el panel: la siguiente factura suya (TC-03 con otro número) ya no escala por HITL-02. El panel muestra quién ("CFO Demo", de `DECIDED_BY`) y cuándo la dio de alta. *(alta con NIT 901.555.010-2; `DC-002` sin NIT y con `Diseno Creativo Bogota SAS` salió `AUTO_APPROVED`; la fila muestra "CFO Demo" y la hora local del navegador)*
- [x] Dar de baja a AWS desde el panel: una factura nueva de AWS escala por HITL-02 ("inactivo"); reactivarlo la deja `AUTO_APPROVED` otra vez. *(baja desde el panel: `AWS-2026-11` escaló por HITL-02 "inactivo", aun con el NIT `US911646860`; tras reactivar, `AWS-VAL-2` salió `AUTO_APPROVED`)*
- [x] Un `tax_id` repetido en el formulario muestra el mensaje del `409`. *(`900584112-4`: "Ya existe un beneficiario con NIT 900584112-4.")*
- [x] Con la API caída: banner de demostración, proveedores del seed en el panel y formulario deshabilitado. *(6 proveedores del seed, "Agregar beneficiario" y los botones de cada fila deshabilitados; en vista móvil la tabla se desplaza dentro de su tarjeta, sin scroll horizontal de la página)*
- [x] Sin errores de JavaScript en la consola (salvo los `409`/`422` provocados a propósito). *(solo los `409`/`422` provocados y los `ERR_CONNECTION_REFUSED` de la prueba con la API caída)*

## Después del merge (producción)

- [ ] Tras el deploy, `GET /api/rules` devuelve `max_payment_usd = 20000` y `GET /api/vendors` lista los proveedores del seed con `active = true` (la migración corrió con `DB_AUTO_MIGRATE=true`).
- [ ] `humo_produccion.py` verde contra producción con TC-08, y el presupuesto de producción queda igual que antes de la corrida.
- [ ] El dashboard público edita el tope y el presupuesto y muestra el panel de beneficiarios sin modo demostración; sin errores en la consola.
- [ ] F7.1 a F7.7 marcados en [roadmap.md](../roadmap.md) con la referencia a esta validación.

## No bloqueante

- Autenticación y roles en los endpoints nuevos (Fase 8): hasta entonces cualquiera con la URL puede editar reglas y beneficiarios, igual que hoy con `POST /api/rules`.
- Historial de cambios de reglas y proveedores.
- Editar `is_pep` y `tax_id`.
