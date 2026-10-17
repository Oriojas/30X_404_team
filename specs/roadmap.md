# Roadmap — Blinka PayAgent (Paybot)

> Parte de la constitución del proyecto, junto con [mission.md](mission.md) y [tech-stack.md](tech-stack.md).
> Orden de implementación en fases muy pequeñas: cada una se puede terminar, probar y commitear sola.
> Al cerrar una fase se marca `[x]`. El cronograma por días y los roles están en [plan_de_trabajo.md](../plan_de_trabajo.md).

**Hitos fijos** (el equipo trabaja entre Colombia, GMT-5, y Tailandia, GMT+7):

| Hito | Colombia (GMT-5) | Tailandia (GMT+7) |
| :--- | :--- | :--- |
| Congelamiento de código | domingo 18-oct-2026, 09:30 AM | domingo 18-oct-2026, 09:30 PM |
| Entrega en HackRadar | domingo 18-oct-2026, antes de las 11:59 AM | domingo 18-oct-2026, antes de las 11:59 PM |

**Orden acordado para lo pendiente:** validaciones y casos trampa → tesorería comprometida → reglas configurables → seguridad y acceso → extensiones si queda tiempo (seguridad adicional, pruebas y CI, multimoneda) → cierre y entrega.

---

## ✅ Completado

- [x] **F0.1 — Monorepo y reglas:** estructura backend/frontend/docs, un solo `.env` y un solo `.gitignore`.
- [x] **F0.2 — Arquitectura hexagonal:** core (domain, ports, use_cases), adaptadores inbound/outbound, composition root y prueba de arquitectura.
- [x] **F0.3 — Esquema y seed:** tablas idempotentes y datos ficticios para TC-01 a TC-06.
- [x] **F0.4 — Tubería de 4 capas:** matriz v3 completa, más FIN-03 e INTEG-04; `REJECTED` corta y las alertas de escalamiento se acumulan.
- [x] **F0.5 — API REST:** listado, carga manual, subida de archivos, decisión humana y reglas.
- [x] **F0.6 — Webhook de Telegram:** extracción de adjuntos, secret token, avisos sin botones.
- [x] **F0.7 — Endurecimiento:** decisión humana atómica, consultas en paralelo, separación del seed de demo.

---

## Fase 1 — OCR real con Gemini (backend)

- [x] **F1.1 — Dependencias:** cambiar `google-generativeai` por `google-genai` en `requirements.txt` y fijar el `GEMINI_MODEL` por defecto (un Flash vigente).
- [x] **F1.2 — Prompt y esquema:** definir el esquema JSON de extracción (número, proveedor, NIT, cuenta, monto, moneda ISO, vencimiento, confianza).
- [x] **F1.3 — Adaptador:** implementar `GeminiOCRAdapter.extract_invoice_data` con el SDK, sin bloquear el event loop.
- [x] **F1.4 — Normalización:** montos con formato latino (`1.500.000,00`), fechas y códigos de moneda.
- [x] **F1.5 — Fallas seguras:** sin API key, con error de red o con JSON inválido, devolver una extracción vacía con confianza 0 (escala por INTEG-03).
- [x] **F1.6 — Pruebas:** unitarias con el cliente simulado (respuesta válida, formato latino, JSON inválido, sin key).
- [x] **F1.7 — Prueba manual:** una factura real en imagen y otra en PDF por `POST /api/invoices/upload`. Quitar del README la nota de "stub". *(Hecho el 17-oct-2026: API + PostgreSQL 16 con seed en Docker + Gemini real; las tres facturas de `backend/tests/fixtures` dieron `AUTO_APPROVED`, `SCALED_TO_HUMAN` (HITL-01) y `REJECTED` (COMP-01). Queda como prueba automática en `test_postgres_integration.py` con el cliente de Gemini simulado.)*

**Listo cuando:** una foto legible de una factura conocida produce la decisión esperada sin carga manual.

## Fase 2 — Ingesta idempotente en todos los canales (backend)

Cualquier canal puede entregar la misma factura más de una vez. Se resuelve en dos niveles: **transporte** (la misma entrega repetida, con el id del canal) y **negocio** (la misma factura por mensajes distintos: INTEG-01, reforzada con el hash del archivo).

- [x] **F2.1 — Esquema:** tabla `ingested_messages (channel, external_id, invoice_id, status, received_at)` con `PRIMARY KEY (channel, external_id)`, y columna `file_sha256` en `invoices`, ambas en `schema.sql`.
- [x] **F2.2 — Puerto genérico:** `IngestionLog` en `core/ports` con `claim(channel, external_id)` (atómico: `INSERT ... ON CONFLICT DO NOTHING`), `complete(..., invoice_id)` y `release(...)`. Adaptador PostgreSQL.
- [x] **F2.3 — Caso de uso:** `ProcessInvoiceUseCase` recibe un `external_id` opcional. Si ya fue reclamado, devuelve la factura existente sin reprocesar ni volver a notificar. Si el procesamiento falla, libera la clave para que el reintento sí se procese.
- [x] **F2.4 — Telegram:** el webhook pasa `update_id` como `external_id`. Un update repetido responde `200 {"status": "duplicate"}` para que Telegram deje de reintentar.
- [x] **F2.5 — Web y API:** `POST /api/invoices/upload` y `POST /api/invoices` aceptan el header `Idempotency-Key`. Una clave repetida devuelve la misma factura (`200`) en vez de crear otra (`201`).
- [x] **F2.6 — Hash del archivo:** calcular el SHA-256 de los documentos (Telegram y web), guardarlo en `invoices.file_sha256` y tratar como duplicado (INTEG-01) un archivo idéntico dentro de la ventana, aunque el OCR no haya leído número ni monto.
- [x] **F2.7 — Pruebas:** la misma clave dos veces por canal, el reintento tras un fallo, solicitudes concurrentes con la misma clave (solo una procesa), el mismo archivo por dos canales distintos y un caso en la integración con PostgreSQL. *(Hecho el 17-oct-2026: 70 pruebas verdes con PostgreSQL 16; ver [validación](2026-10-17-ingesta-idempotente/validation.md).)*

**Listo cuando:** repetir una entrega por cualquier canal no crea una segunda factura ni un aviso duplicado, y el mismo archivo enviado por otro canal queda frenado por INTEG-01.

## Fase 3 — Integración del frontend con la API real (frontend, Oscar)

- [x] **F3.1 — Listado real:** el Audit Log consume `GET /api/invoices` y muestra `evaluations` capa por capa.
- [x] **F3.2 — Estados nuevos:** badges y filtros para `HUMAN_APPROVED` y `HUMAN_REJECTED`; métrica de autonomía sin contar las decisiones humanas.
- [x] **F3.3 — Decisión humana:** los botones del Drawer llaman a `POST /api/invoices/{id}/decision` (con `decided_by` y una nota) y manejan el `409`.
- [x] **F3.4 — Subida de facturas:** botón de carga hacia `POST /api/invoices/upload`, con estado de procesamiento y resultado.
- [x] **F3.5 — Idempotency-Key:** generar un UUID (`crypto.randomUUID()`) por cada intento de subida, enviarlo en el header `Idempotency-Key` y reutilizarlo en los reintentos del mismo archivo. Deshabilitar el botón mientras se procesa, para evitar el doble clic. Tratar el `200` (factura ya existente) igual que el `201`.
- [x] **F3.6 — Reglas:** el panel de reglas persiste con `POST /api/rules` y muestra los errores de validación. *(Hecho el 17-oct-2026: recorrido manual con PostgreSQL 16 y seed, TC-01 a TC-06 y aprobación de un escalamiento desde el navegador; ver [validación](2026-10-17-frontend-api-real/validation.md).)*

**Listo cuando:** se puede recorrer TC-01 a TC-06 y aprobar un escalamiento solo desde el navegador.

## Fase 4 — Despliegue en Railway

- [x] **F4.1 — Backend:** servicio desde `backend/Dockerfile` con `DATABASE_URL`, `DB_AUTO_MIGRATE=true` y `DB_SEED_DEMO=true` (demo). *(Hecho el 17-oct-2026: definido en `.railway/railway.ts` (IaC), en línea en `https://backend-production-ea088.up.railway.app` con Postgres y el seed.)*
- [x] **F4.2 — Secretos:** `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` y `ALLOWED_ORIGINS` con la URL del frontend. *(Hecho el 17-oct-2026: secretos cargados en Railway, nunca en el repo.)*
- [x] **F4.3 — Webhook:** registrar `setWebhook` con la URL pública y el `secret_token`. *(Hecho el 17-oct-2026: `backend/scripts/registrar_webhook.py`; una factura real por Telegram llegó y se escaló.)*
- [x] **F4.4 — Frontend:** servicio desde `frontend/Dockerfile` con `VITE_API_BASE_URL` apuntando al backend. *(Hecho el 17-oct-2026: `ARG VITE_API_BASE_URL` en el Dockerfile y Nginx sin proxy; `https://30x404team-production.up.railway.app` consume el backend real sin modo demostración.)*
- [x] **F4.5 — Humo en producción:** `/api/health` conectado, Test Suite por la API, una factura por Telegram y otra por la web. *(Hecho el 17-oct-2026: `scripts/humo_produccion.py` 9/9, subida web, aprobación, reglas y reenvío por Telegram frenado por INTEG-01; ver [validación](2026-10-17-despliegue-railway/validation.md).)*

**Listo cuando:** el jurado puede abrir la URL pública y probar el agente sin ayuda.

## Fase 4.1 — Tesorería real en el dashboard

Hallazgo de la validación de la Fase 4: el hero y la tarjeta de colchón mostraban valores del diseño de prueba ($48,250 de caja, $10,000 de colchón), no los que usa el agente. Ver [requisitos](2026-10-17-tesoreria-real/requirements.md).

- [x] **T1 — Endpoint:** `GET /api/treasury` con saldo, presupuesto mensual y gasto aprobado del mes.
- [x] **T2 — Cliente:** `DEFAULT_RULES` con el colchón real del backend (`1000`) y la tesorería cargada al abrir el dashboard.
- [x] **T3 — Hero y tarjeta de colchón:** caja, colchón, umbral y holgura reales; la holgura sigue a la reserva mientras se edita. *(Hecho el 17-oct-2026: validado en local y en producción tras el merge de #14; ver [validación](2026-10-17-tesoreria-real/validation.md).)*

**Listo cuando:** el dashboard público muestra la misma caja y el mismo colchón con los que decide el agente.

## Fase 5 — Validaciones pendientes, casos trampa y CI

Pruebas recomendadas de las Fases 2, 3 y 4 que quedaron sin marcar porque faltaba el despliegue, y el caso trampa de "no cuadra con lo acordado", que aún no está en la Test Suite de la demo.

- [x] **F5.1 — Aviso de la decisión humana:** enviar una factura por Telegram, aprobarla desde el Drawer del dashboard público y confirmar que el chat recibe el aviso del resultado (principio 4 de [mission.md](mission.md)). *(Hecho el 17-oct-2026: NA-4521 por Telegram, aprobada desde el Drawer; el chat recibió el aviso.)*
- [x] **F5.2 — Update repetido:** reenviar con `curl` el mismo cuerpo de un update al webhook de producción (con el secret) y confirmar `200 {"status": "duplicate"}` y un solo aviso en el chat. *(Hecho el 17-oct-2026: `200 duplicate` con el `update_id` 239648102, sin factura ni aviso nuevos.)*
- [x] **F5.3 — Hash entre canales:** subir por la web un archivo que ya llegó por Telegram y ver el rechazo por INTEG-01 en el dashboard. *(Hecho el 17-oct-2026: factura 22 `REJECTED` por INTEG-01.)*
- [x] **F5.4 — Marcar lo ya cubierto:** `Idempotency-Key` `201` → `200` (segunda corrida de `humo_produccion.py`) y build con `frontend/Dockerfile` (Fase 4), con la referencia en cada `validation.md`. *(Hecho el 17-oct-2026.)*
- [x] **F5.5 — TC-07:** agregar a `casos_demo.py`, `humo_produccion.py` y la Test Suite de [reglas_pago_agente_v3.md](../docs/reglas-negocio/reglas_pago_agente_v3.md) el caso trampa "factura que no cuadra con lo acordado" (TC-07, `SCALED_TO_HUMAN` por INTEG-02). El caso trampa de presupuesto (TC-08) depende de poder editar el presupuesto y queda en F7.6. *(Hecho el 17-oct-2026: AWS por $1,500 contra una tarifa de $1,000; PR #17.)*
- [x] **F5.6 — Datos para el pitch:** tiempo de arranque en frío del backend y captura del dashboard en producción. *(Hecho el 17-oct-2026: el contenedor arranca en 0.7 s y el redeploy tarda 25 s; capturas en `docs/pitch_presentacion/`.)*
- [x] **F5.7 — CI:** workflow de GitHub Actions que corre `pytest` con los fakes (las pruebas de integración se omiten sin `TEST_DATABASE_URL`) y `npm run build` en cada PR. El servicio de PostgreSQL en el CI queda en F9.6. *(Hecho el 17-oct-2026: `.github/workflows/ci.yml`, en verde en PR #17 y en `master`; ver [validación](2026-10-17-validaciones-casos-trampa-ci/validation.md).)*

**Listo cuando:** las verificaciones recomendadas de las Fases 2 a 4 están marcadas con evidencia, la demo cubre los casos trampa del reto que ya permite el código (duplicado, beneficiario nuevo, no cuadra con lo acordado, monto sobre el límite, saldo insuficiente) y cada PR muestra el resultado de las pruebas.

## Fase 6 — Tesorería comprometida

El reto descalifica a quien apruebe un pago indebido. Hoy FIN-01 compara cada factura contra el saldo total por separado y la aprobación humana no vuelve a revisar la solvencia: con $8,500 de caja, cinco facturas de $1,900 de proveedores con historial salen `AUTO_APPROVED` aunque suman $9,500.

- [ ] **F6.1 — Saldo como foto con fecha:** como no hay estado de pago ejecutado (el reto no mueve dinero), `treasury_accounts.balance_usd` es el saldo a la fecha de `treasury_accounts.updated_at`. Se compromete solo lo aprobado **después** de esa fecha: `disponible = saldo − Σ usd_amount de AUTO_APPROVED y HUMAN_APPROVED con fecha de aprobación (processed_at o decided_at) > updated_at`. El historial del seed (anterior a la foto) no compromete nada, así que TC-01 sigue `AUTO_APPROVED`. `PATCH /api/treasury` con el saldo toma una foto nueva (también actualiza `updated_at`) y libera lo comprometido; `casos_demo.py` y `humo_produccion.py` lo llaman antes de TC-01 para que las aprobaciones de corridas anteriores no hagan escalar la demo. `updated_at` se escribe siempre con `timezone('UTC', now())` (schema, seed y `UPDATE`), igual que las fechas de las facturas.
- [ ] **F6.2 — Solvencia con el disponible:** FIN-01 y FIN-03 evalúan contra el disponible y la explicación cita saldo, comprometido y disponible. FIN-02 suma el gasto del mes con la misma fecha de aprobación que F6.1 (`processed_at` en `AUTO_APPROVED`, `decided_at` en `HUMAN_APPROVED`).
- [ ] **F6.3 — Revalidación al aprobar:** `DecideInvoiceUseCase` recibe los puertos `TreasuryRepository` y `RulesRepository` (cableados en `container.py`) y recalcula la Capa 3 antes de un `HUMAN_APPROVED`. La persona siempre puede aprobar: el Audit Log registra el disponible y las alertas FIN vigentes al aprobar, como excepción aprobada por esa persona. La única excepción es una factura sin conversión a USD (INTEG-04, `usd_amount = 0`): responde `409`, porque comprometería $0 con un monto real desconocido; solo se puede rechazar. La variante estricta (`409` ante una alerta FIN nueva desde el escalamiento) queda en F9.7.
- [ ] **F6.4 — Serializar la solvencia:** dos ingestas simultáneas (Telegram y web), o una ingesta y una aprobación, leen el mismo disponible. La lectura de tesorería, la evaluación y el guardado se serializan con **una sola** instancia de `asyncio.Lock` creada en `container.py` e inyectada en `ProcessInvoiceUseCase`, `DecideInvoiceUseCase` y el `PATCH /api/treasury` (el OCR queda fuera del candado). Vale porque el backend corre en una sola réplica en Railway; con más réplicas se cambia por `pg_advisory_xact_lock`, y la limitación queda documentada en el README.
- [ ] **F6.5 — Endpoint y dashboard:** `GET /api/treasury` agrega `committed_usd`, `available_usd` y la fecha de la foto; el hero muestra el disponible y una tarjeta muestra el presupuesto mensual y el gasto del mes (FIN-02).
- [ ] **F6.6 — Pruebas:** varias facturas que caben solas pero no juntas (la que desborda escala por FIN-01); historial anterior a la foto que no compromete; aprobación humana de TC-05 como excepción registrada; `409` al aprobar una factura INTEG-04; dos ingestas concurrentes de $4,000 con $8,500 de saldo y $1,000 de colchón (solo una sale `AUTO_APPROVED`). Las pruebas que construyen `DecideInvoiceUseCase(invoices, notifier)` se adaptan a los puertos nuevos en la misma fase. Antes de mergear, `test_postgres_integration.py` corre en local con PostgreSQL 16 en Docker: lo comprometido, la fecha de FIN-02 y el UTC son SQL que los fakes no cubren. TC-01 a TC-07 siguen dando lo esperado.

**Listo cuando:** el agente nunca aprueba solo un pago que deje lo comprometido por encima del saldo o del presupuesto, ni siquiera con ingestas simultáneas, y cada pago que una persona aprueba fuera de esos límites queda registrado como excepción aprobada por ella.

## Fase 7 — Reglas configurables completas

El reto pide una pantalla donde la empresa define sus reglas: límites por pago y por periodo, beneficiarios permitidos y aprobación humana por encima de cierto monto. Hoy solo el umbral de aprobación, el colchón, la ventana de duplicados y SARLAFT se editan; el presupuesto, los beneficiarios y las tarifas acordadas viven solo en el seed.

- [ ] **F7.1 — Presupuesto del periodo:** `monthly_budget_usd` vive en `treasury_accounts` (`TreasuryRepository`), no en `company_rules`: si se agregara a `CompanyRulesUpdate`, `UpdateRulesUseCase` lo descartaría en silencio. Se edita con el `PATCH /api/treasury` de F6.1 (con validación `422`); el panel de reglas lo muestra junto a los demás umbrales pero lo guarda por esa ruta. FIN-02 lo usa en la siguiente evaluación.
- [ ] **F7.2 — Tope duro por pago:** nueva regla `max_payment_usd` en `company_rules`; una factura por encima queda `REJECTED` con un código nuevo (FIN-04), distinta del umbral de aprobación humana (HITL-01). Validar que `max_payment_usd ≥ max_autonomous_usd` y documentar la regla en [reglas_pago_agente_v3.md](../docs/reglas-negocio/reglas_pago_agente_v3.md).
- [ ] **F7.3 — Beneficiarios permitidos:** columna `vendors.active BOOLEAN DEFAULT TRUE` en `schema.sql` y `Vendor.active` en el dominio; `GET`/`POST`/`PATCH /api/vendors` para alta, edición (cuenta autorizada y tarifa acordada, que usan COMP-02 e INTEG-02) y baja lógica (`active = false`). `VendorRepository.find` sigue devolviendo el proveedor inactivo, para que COMP-02, COMP-04 e INTEG-02 sigan evaluándose contra su registro; es HITL-02 quien mira `active`. `vendors` e `invoices` siguen sin `company_id` (MVP de una empresa, igual que hoy); el modelo multiempresa queda para V4.
- [ ] **F7.4 — HITL-02 = lista permitida:** el reto define el caso trampa como "beneficiario que no está en la lista permitida". HITL-02 pasa a dispararse cuando el proveedor no está registrado o está inactivo, y deja de exigir historial de pagos: el alta desde el dashboard por un aprobador es la verificación inicial y queda en el registro con quién y cuándo. Se documenta el cambio en [reglas_pago_agente_v3.md](../docs/reglas-negocio/reglas_pago_agente_v3.md); TC-03 (proveedor fuera de la lista) sigue escalando por HITL-02.
- [ ] **F7.5 — Panel en el dashboard:** tabla de beneficiarios con su cuenta, tarifa acordada y estado, y formulario de alta y edición; todas las llamadas por `api.js`.
- [ ] **F7.6 — TC-08:** caso trampa "presupuesto del periodo insuficiente" (`SCALED_TO_HUMAN` por FIN-02) en `casos_demo.py`, `humo_produccion.py` y la Test Suite. Para que FIN-02 dispare sin FIN-01 ni FIN-03, el script baja el presupuesto con F7.1 justo por debajo de `gasto del mes + monto`, envía una factura de un proveedor de la lista, dentro de su tarifa y del umbral autónomo, y restaura el presupuesto (como se probó la ventana de duplicados en la Fase 4). No se infla el gasto del seed: con la Fase 6 ese gasto comprometería el saldo y dispararía FIN-01 en todos los casos.
- [ ] **F7.7 — Pruebas:** validaciones `422`; un cambio de presupuesto, tope o tarifa que cambia la decisión de la siguiente factura; un proveedor dado de alta desde el dashboard cuya siguiente factura ya no escala por HITL-02; un proveedor dado de baja que vuelve a escalar por HITL-02 y conserva COMP-02/INTEG-02; TC-01 a TC-08 dan lo esperado. En la misma fase se adaptan las pruebas que esperan HITL-02 para un proveedor registrado sin historial (`test_process_invoice.py`, `test_ingestion_idempotency.py`) y se borran `vendor_has_paid_history` y el comentario del seed sobre HITL-02, para que el CI de F5.7 siga en verde.

**Listo cuando:** desde el dashboard se definen el límite por pago, el umbral de aprobación humana, el presupuesto del periodo y los beneficiarios con su tarifa acordada, y la siguiente factura se evalúa con esos valores.

## Fase 8 — Seguridad e inicio de sesión

Hoy ningún endpoint exige autenticación: cualquiera con la URL del backend puede cambiar las reglas (incluso desactivar SARLAFT), aprobar facturas escaladas con un `decided_by` arbitrario o gastar cuota de Gemini. El jurado debe seguir pudiendo probar sin ayuda, así que las credenciales de demo se publican.

- [ ] **F8.1 — Usuarios y roles:** dos roles con credenciales de demo en variables de entorno, comparadas con `hmac.compare_digest` (son públicas, así que no hace falta hash): `operador` (sube facturas) y `aprobador` (decide escalamientos, edita reglas y beneficiarios). La segregación queda por rol: el operador no puede aprobar.
- [ ] **F8.2 — Token:** `POST /api/auth/login` entrega un token firmado (HMAC/JWT) con expiración; una dependencia de FastAPI lo exige en `POST /api/rules`, en los endpoints de beneficiarios de la Fase 7, en `POST /api/invoices`, `POST /api/invoices/upload` y `POST /api/invoices/{id}/decision`. Los `GET` siguen públicos. La clave que firma los tokens (`AUTH_SECRET`) sí es secreta: se carga en Railway y se declara con `preserve()` en `.railway/railway.ts`. Solo toca adaptadores de entrada y `config.py`, no el Core.
- [ ] **F8.3 — Autor verificado:** `decided_by` sale del token, no del cuerpo de la solicitud; el Audit Log registra el usuario autenticado.
- [ ] **F8.4 — Frontend:** pantalla de login con las credenciales de demo visibles, token en memoria, header `Authorization` en `api.js` y manejo de `401`/`403` (los botones del rol que falta quedan deshabilitados).
- [ ] **F8.5 — Endurecimiento mínimo:** tope a `limit` en `GET /api/invoices`. `/docs` sigue encendido: con el token de la Fase 8, Swagger no permite cambiar nada sin credenciales y es la forma más fácil de que el jurado pruebe la API. El resto del endurecimiento queda en F9.2.
- [ ] **F8.6 — Pruebas:** `401` sin token, `403` con el rol equivocado, `decided_by` tomado del token y humo de producción actualizado para autenticarse.

**Listo cuando:** sin credenciales no se pueden cambiar reglas ni beneficiarios ni decidir facturas, el operador no puede aprobar, y el jurado entra con las credenciales de demo publicadas y recorre TC-01 a TC-08.

## Fase 9 — Extensiones (si queda tiempo)

Trabajo valioso que se retiró de las Fases 6 y 8 para que el plan quepa antes del congelamiento, más la multimoneda. Solo se empieza cuando las Fases 5 a 8 estén mergeadas y en producción, y nunca se come la ventana de la Fase 10 (domingo desde las 05:00 AM en Colombia / 05:00 PM en Tailandia). Cada bloque va en su propia rama y se mergea solo si cierra completo. Lo que no se alcance pasa sin cambios a la visión posterior al Demo Day. Orden sugerido: 9A y 9B son cortos; 9C es el más largo y el más arriesgado.

### 9A — Seguridad adicional

- [ ] **F9.1 — Segregación por persona:** columna `invoices.submitted_by`, llenada por cada canal: el usuario del token en web y API, y `telegram:<chat_id>` en Telegram. `DecideInvoiceUseCase` rechaza la decisión si `decided_by == submitted_by` (regla del Core, con su error de dominio → `403`). Limitación documentada: un chat de Telegram no está ligado a un usuario del dashboard, así que un aprobador que envía por Telegram y aprueba desde el dashboard no se detecta; el Audit Log sí muestra quién envió y quién aprobó.
- [ ] **F9.2 — Endurecimiento completo:** `/docs` y `/openapi.json` apagados en producción (si el jurado ya no los necesita), verificación de los bytes del archivo (firma de JPG/PNG/WEBP/PDF), del `mime_type` y del tamaño de los documentos de Telegram, y `ALLOWED_ORIGINS` sin `*` por defecto en `config.py`.
- [ ] **F9.3 — Límite de uso:** límite de solicitudes por IP en la subida web y por chat en Telegram, para proteger la cuota de Gemini.
- [ ] **F9.4 — Contenedores:** backend sin root y sin `build-essential` en la imagen final; Nginx con cabeceras `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` y `Referrer-Policy`.
- [ ] **F9.5 — Contraseñas con hash:** guardar las credenciales en las variables de entorno como hash (bcrypt o `hashlib.scrypt`) en vez de compararlas en claro, para cuando dejen de ser credenciales de demo.

### 9B — Pruebas y CI adicionales

- [ ] **F9.6 — PostgreSQL en el CI:** servicio de PostgreSQL 16 en GitHub Actions con `TEST_DATABASE_URL`, para que `test_postgres_integration.py` corra en cada PR y no solo en local.
- [ ] **F9.7 — Revalidación estricta:** al aprobar, distinguir las alertas FIN que la factura ya traía al escalar de las nuevas; ante una alerta FIN **nueva** (otro pago consumió el saldo o el presupuesto), responder `409` con la razón y dejar la factura en `SCALED_TO_HUMAN` para que el aprobador decida con la información vigente. Con su prueba.
- [ ] **F9.8 — Aprobaciones concurrentes:** prueba de dos aprobaciones simultáneas que no pueden comprometer más que el disponible (el candado de F6.4 ya las serializa; falta la prueba).

### 9C — Tesorería multimoneda

El reto menciona los pagos en otra moneda como parte del dolor actual, pero no la exige. La cuenta Blinka tiene billeteras por moneda. Una factura en COP se paga primero desde la billetera COP y, si no alcanza, desde USD con conversión explícita a $0.00 FX Markup. Los umbrales siguen en USD (principio 5 de [mission.md](mission.md)).

- [ ] **F9.9 — Esquema:** tabla `treasury_balances (company_id, currency, balance, updated_at)` con `PRIMARY KEY (company_id, currency)` como **única** fuente de saldos. `schema.sql` migra `treasury_accounts.balance_usd` a la fila USD si no existe, y desde ahí `treasury_accounts` solo guarda el presupuesto; nadie vuelve a leer `balance_usd` (se puede borrar después del Demo Day). Saldos ficticios en `seed.sql` (USD, COP, MXN). Cada billetera tiene su propia foto (`updated_at`), igual que en F6.1.
- [ ] **F9.10 — Compromisos por billetera:** columnas `invoices.payment_wallet` (moneda de la billetera elegida) y `invoices.payment_amount` (monto en esa moneda). Lo comprometido se calcula por billetera: una factura en COP pagada desde COP descuenta pesos de la billetera COP y no toca la de USD; una que cae a USD descuenta su equivalente en USD. `TreasuryStatus` expone los disponibles por moneda y el total equivalente en USD; el Core decide la fuente del pago (billetera local o USD) y la guarda en la factura.
- [ ] **F9.11 — Solvencia:** FIN-01 y FIN-03 evalúan contra la billetera de la moneda de la factura y, si no alcanza, contra USD convertido; el Audit Log registra la billetera usada y la tasa aplicada.
- [ ] **F9.12 — Tasas en vivo con respaldo:** `FXRateProvider` contra una API de tasas, con las tasas fijas como respaldo ante error o timeout; la fuente de la tasa queda en el registro. Se agrega a [tech-stack.md](tech-stack.md) en el mismo cambio.
- [ ] **F9.13 — Endpoint y dashboard:** `GET /api/treasury` devuelve el desglose por moneda y el hero muestra cada billetera y el total en USD.
- [ ] **F9.14 — Pruebas:** factura COP pagada desde la billetera COP, dos facturas COP seguidas (la segunda ve la billetera COP ya comprometida y la de USD intacta), factura COP que cae a USD, moneda sin billetera ni tasa (escala por INTEG-04) y falla del proveedor de tasas (usa las fijas); TC-01 a TC-08 siguen dando lo esperado.

**Listo cuando** (por bloque): 9A, los endpoints y contenedores cumplen lo descrito con sus pruebas; 9B, el CI corre las pruebas de integración y la revalidación estricta está probada; 9C, el dashboard muestra los saldos por moneda y cada decisión explica desde qué billetera se pagaría y con qué tasa.


## Fase 10 — Cierre y entrega

- [ ] **F10.1 — Limpieza:** quitar dependencias sin uso (`python-telegram-bot`) y pasar `pytest` a desarrollo.
- [ ] **F10.2 — Congelamiento:** último commit antes del domingo 09:30 AM (Colombia) / 09:30 PM (Tailandia).
- [ ] **F10.3 — README final:** link de la demo desplegada, credenciales de demo por rol y guía de prueba para el jurado con TC-01 a TC-08.
- [ ] **F10.4 — Video pitch (3 min):** problema, demo en vivo (Telegram + dashboard) e impacto, contado con los tres criterios del reto (autonomía, seguridad y explicabilidad). La capa de Compliance (OFAC, PEP, SARLAFT) se presenta como opcional: el reto deja fuera las decisiones de cumplimiento.
- [ ] **F10.5 — Entrega:** formulario de HackRadar antes del domingo 11:59 AM (Colombia) / 11:59 PM (Tailandia).

---

## Después del Demo Day (visión, sin fecha)

Fases candidatas, en orden sugerido, alineadas con la visión de [mission.md](mission.md):

- [ ] **V1 — Canal de correo:** adaptador de entrada de email que reutiliza `ProcessInvoiceUseCase`.
- [ ] **V2 — Tasas en vivo:** movida a las extensiones (F9.12, si queda tiempo). Queda para después: elegir un proveedor de tasas con SLA y cachear las tasas.
- [ ] **V3 — Tesorería real:** saldos por billetera y movimientos leídos desde la cuenta Blinka (F9.9 a F9.14 los modelan con datos ficticios).
- [ ] **V4 — Multiempresa y roles:** reglas, proveedores y aprobadores por empresa. La autenticación y los dos roles de demo llegan en la Fase 8; queda la gestión de usuarios real (alta, baja, SSO) y los roles por empresa.
- [ ] **V5 — Canal de WhatsApp.**
- [ ] **V6 — Ejecución de pagos vía Blinka:** programar el pago al aprobar, manteniendo el Audit Log.
