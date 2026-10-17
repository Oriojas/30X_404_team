# Roadmap — Blinka PayAgent (Paybot)

> Parte de la constitución del proyecto, junto con [mission.md](mission.md) y [tech-stack.md](tech-stack.md).
> Orden de implementación en fases muy pequeñas: cada una se puede terminar, probar y commitear sola.
> Al cerrar una fase se marca `[x]`. El cronograma por días y los roles están en [plan_de_trabajo.md](../plan_de_trabajo.md).

**Hitos fijos** (el equipo trabaja entre Colombia, GMT-5, y Tailandia, GMT+7):

| Hito | Colombia (GMT-5) | Tailandia (GMT+7) |
| :--- | :--- | :--- |
| Congelamiento de código | domingo 18-oct-2026, 09:30 AM | domingo 18-oct-2026, 09:30 PM |
| Entrega en HackRadar | domingo 18-oct-2026, antes de las 11:59 AM | domingo 18-oct-2026, antes de las 11:59 PM |

**Orden acordado para lo pendiente:** validaciones pendientes → seguridad y acceso → tesorería comprometida → multimoneda → cierre y entrega.

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

## Fase 5 — Validaciones pendientes y CI

Pruebas recomendadas de las Fases 2, 3 y 4 que quedaron sin marcar porque faltaba el despliegue. Ventana sugerida: sábado 07:00–08:30 AM (Colombia) / 07:00–08:30 PM (Tailandia).

- [ ] **F5.1 — Aviso de la decisión humana:** enviar una factura por Telegram, aprobarla desde el Drawer del dashboard público y confirmar que el chat recibe el aviso del resultado (principio 4 de [mission.md](mission.md)).
- [ ] **F5.2 — Update repetido:** reenviar con `curl` el mismo cuerpo de un update al webhook de producción (con el secret) y confirmar `200 {"status": "duplicate"}` y un solo aviso en el chat.
- [ ] **F5.3 — Hash entre canales:** subir por la web un archivo que ya llegó por Telegram y ver el rechazo por INTEG-01 en el dashboard.
- [ ] **F5.4 — Marcar lo ya cubierto:** `Idempotency-Key` `201` → `200` (segunda corrida de `humo_produccion.py`) y build con `frontend/Dockerfile` (Fase 4), con la referencia en cada `validation.md`.
- [ ] **F5.5 — Datos para el pitch:** tiempo de arranque en frío del backend y captura del dashboard en producción.
- [ ] **F5.6 — CI:** workflow de GitHub Actions que corre `pytest` con un servicio de PostgreSQL 16 (`TEST_DATABASE_URL`) y `npm run build` en cada PR.

**Listo cuando:** las verificaciones recomendadas de las Fases 2 a 4 están marcadas con evidencia y cada PR muestra el resultado de las pruebas.

## Fase 6 — Seguridad e inicio de sesión

Hoy ningún endpoint exige autenticación: cualquiera con la URL del backend puede cambiar las reglas (incluso desactivar SARLAFT), aprobar facturas escaladas con un `decided_by` arbitrario o gastar cuota de Gemini. El jurado debe seguir pudiendo probar sin ayuda, así que las credenciales de demo se publican. Ventana sugerida: sábado 08:30 AM – domingo 00:30 AM (Colombia) / sábado 08:30 PM – domingo 12:30 PM (Tailandia), con pausa para dormir.

- [ ] **F6.1 — Usuarios y roles:** dos roles con credenciales de demo en variables de entorno (contraseña con hash): `operador` (sube facturas) y `aprobador` (decide escalamientos y edita reglas). Segregación de funciones: quien sube no aprueba.
- [ ] **F6.2 — Token:** `POST /api/auth/login` entrega un token firmado (HMAC/JWT) con expiración; una dependencia de FastAPI lo exige en `POST /api/rules`, `POST /api/invoices`, `POST /api/invoices/upload` y `POST /api/invoices/{id}/decision`. Los `GET` siguen públicos. Solo toca adaptadores de entrada y `config.py`, no el Core.
- [ ] **F6.3 — Autor verificado:** `decided_by` sale del token, no del cuerpo de la solicitud; el Audit Log registra el usuario autenticado.
- [ ] **F6.4 — Frontend:** pantalla de login con las credenciales de demo visibles, token en memoria, header `Authorization` en `api.js` y manejo de `401`/`403` (los botones del rol que falta quedan deshabilitados).
- [ ] **F6.5 — Endurecimiento de la API:** `/docs` y `/openapi.json` apagados en producción, tope a `limit` en `GET /api/invoices`, `ALLOWED_ORIGINS` sin `*` por defecto, verificación de los bytes del archivo (firma de JPG/PNG/WEBP/PDF) y del `mime_type` y tamaño de los documentos de Telegram.
- [ ] **F6.6 — Límite de uso:** límite de solicitudes por IP en la subida web y por chat en Telegram, para proteger la cuota de Gemini.
- [ ] **F6.7 — Contenedores:** backend sin root y sin `build-essential` en la imagen final; Nginx con cabeceras `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` y `Referrer-Policy`.
- [ ] **F6.8 — Pruebas:** `401` sin token, `403` con el rol equivocado, `decided_by` tomado del token y humo de producción actualizado para autenticarse.

**Listo cuando:** sin credenciales no se pueden cambiar reglas ni decidir facturas, y el jurado entra con las credenciales de demo publicadas y recorre TC-01 a TC-06.

## Fase 7 — Tesorería comprometida

FIN-01 compara cada factura contra el saldo total por separado, y la aprobación humana no vuelve a revisar la solvencia: con $8,500 de caja, tres facturas de $3,000 pasan una por una. Ventana sugerida: domingo 00:30–03:00 AM (Colombia) / domingo 12:30–03:00 PM (Tailandia).

- [ ] **F7.1 — Saldo disponible:** `disponible = saldo − aprobado pendiente de pago` (`AUTO_APPROVED` + `HUMAN_APPROVED`); FIN-01 y FIN-03 evalúan contra el disponible y la explicación lo cita.
- [ ] **F7.2 — Revalidación al aprobar:** `DecideInvoiceUseCase` vuelve a evaluar FIN-01 y FIN-03 antes de un `HUMAN_APPROVED`; si ya no hay saldo, responde `409` con la razón y la factura sigue `SCALED_TO_HUMAN`.
- [ ] **F7.3 — Endpoint y dashboard:** `GET /api/treasury` agrega `committed_usd` y `available_usd`; el hero muestra el disponible y una tarjeta muestra el presupuesto mensual y el gasto del mes (FIN-02).
- [ ] **F7.4 — Pruebas:** dos facturas que caben solas pero no juntas (la segunda escala por FIN-01) y una aprobación humana rechazada por falta de saldo; TC-01 a TC-06 siguen dando lo esperado.

**Listo cuando:** la suma de lo aprobado nunca supera el saldo de la cuenta, ni por el agente ni por un aprobador.

## Fase 8 — Tesorería multimoneda

La cuenta Blinka tiene billeteras por moneda. Una factura en COP se paga primero desde la billetera COP y, si no alcanza, desde USD con conversión explícita a $0.00 FX Markup. Los umbrales siguen en USD (principio 5 de [mission.md](mission.md)). Ventana sugerida: domingo 03:00–07:00 AM (Colombia) / domingo 03:00–07:00 PM (Tailandia). Si no cierra a tiempo, queda en su rama sin mergear y no bloquea la entrega.

- [ ] **F8.1 — Esquema:** tabla `treasury_balances (company_id, currency, balance)` con `PRIMARY KEY (company_id, currency)` en `schema.sql`, y saldos ficticios en `seed.sql` (USD, COP, MXN), sin romper `treasury_accounts`.
- [ ] **F8.2 — Dominio:** `TreasuryStatus` con saldos por moneda y el disponible total equivalente en USD; el Core decide la fuente del pago (billetera local o USD).
- [ ] **F8.3 — Solvencia:** FIN-01 y FIN-03 evalúan contra la billetera de la moneda de la factura y, si no alcanza, contra USD convertido; el Audit Log registra la billetera usada y la tasa aplicada.
- [ ] **F8.4 — Tasas en vivo con respaldo:** `FXRateProvider` contra una API de tasas, con las tasas fijas como respaldo ante error o timeout; la fuente de la tasa queda en el registro. Se agrega a [tech-stack.md](tech-stack.md) en el mismo cambio.
- [ ] **F8.5 — Endpoint y dashboard:** `GET /api/treasury` devuelve el desglose por moneda y el hero muestra cada billetera y el total en USD.
- [ ] **F8.6 — Pruebas:** factura COP pagada desde la billetera COP, factura COP que cae a USD, moneda sin billetera ni tasa (escala por INTEG-04) y falla del proveedor de tasas (usa las fijas); TC-01 a TC-06 siguen dando lo esperado.

**Listo cuando:** el dashboard muestra los saldos por moneda y cada decisión explica desde qué billetera se pagaría y con qué tasa.

## Fase 9 — Cierre y entrega

- [ ] **F9.1 — Limpieza:** quitar dependencias sin uso (`python-telegram-bot`) y pasar `pytest` a desarrollo.
- [ ] **F9.2 — Congelamiento:** último commit antes del domingo 09:30 AM (Colombia) / 09:30 PM (Tailandia).
- [ ] **F9.3 — README final:** link de la demo desplegada, credenciales de demo por rol y guía de prueba para el jurado.
- [ ] **F9.4 — Video pitch (3 min):** problema, demo en vivo (Telegram + dashboard) e impacto.
- [ ] **F9.5 — Entrega:** formulario de HackRadar antes del domingo 11:59 AM (Colombia) / 11:59 PM (Tailandia).

---

## Después del Demo Day (visión, sin fecha)

Fases candidatas, en orden sugerido, alineadas con la visión de [mission.md](mission.md):

- [ ] **V1 — Canal de correo:** adaptador de entrada de email que reutiliza `ProcessInvoiceUseCase`.
- [ ] **V2 — Tasas en vivo:** adelantada a la Fase 8 (F8.4). Queda para después: elegir un proveedor de tasas con SLA y cachear las tasas.
- [ ] **V3 — Tesorería real:** saldos por billetera y movimientos leídos desde la cuenta Blinka (la Fase 8 los modela con datos ficticios).
- [ ] **V4 — Multiempresa y roles:** reglas, proveedores y aprobadores por empresa. La autenticación y los dos roles de demo llegan en la Fase 6; queda la gestión de usuarios real (alta, baja, SSO) y los roles por empresa.
- [ ] **V5 — Canal de WhatsApp.**
- [ ] **V6 — Ejecución de pagos vía Blinka:** programar el pago al aprobar, manteniendo el Audit Log.
