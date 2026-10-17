# Roadmap — Blinka PayAgent (Paybot)

> Parte de la constitución del proyecto, junto con [mission.md](mission.md) y [tech-stack.md](tech-stack.md).
> Orden de implementación en fases muy pequeñas: cada una se puede terminar, probar y commitear sola.
> Al cerrar una fase se marca `[x]`. El cronograma por días y los roles están en [plan_de_trabajo.md](../plan_de_trabajo.md).

**Hitos fijos:** congelamiento de código el **domingo 18 de octubre de 2026 a las 09:30 AM** y entrega en HackRadar antes de las **11:59 AM**.

**Orden acordado para lo pendiente:** OCR real → ingesta idempotente → integración del frontend → despliegue en Railway.

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

- [ ] **F3.1 — Listado real:** el Audit Log consume `GET /api/invoices` y muestra `evaluations` capa por capa.
- [ ] **F3.2 — Estados nuevos:** badges y filtros para `HUMAN_APPROVED` y `HUMAN_REJECTED`; métrica de autonomía sin contar las decisiones humanas.
- [ ] **F3.3 — Decisión humana:** los botones del Drawer llaman a `POST /api/invoices/{id}/decision` (con `decided_by` y una nota) y manejan el `409`.
- [ ] **F3.4 — Subida de facturas:** botón de carga hacia `POST /api/invoices/upload`, con estado de procesamiento y resultado.
- [ ] **F3.5 — Idempotency-Key:** generar un UUID (`crypto.randomUUID()`) por cada intento de subida, enviarlo en el header `Idempotency-Key` y reutilizarlo en los reintentos del mismo archivo. Deshabilitar el botón mientras se procesa, para evitar el doble clic. Tratar el `200` (factura ya existente) igual que el `201`.
- [ ] **F3.6 — Reglas:** el panel de reglas persiste con `POST /api/rules` y muestra los errores de validación.

**Listo cuando:** se puede recorrer TC-01 a TC-06 y aprobar un escalamiento solo desde el navegador.

## Fase 4 — Despliegue en Railway

- [ ] **F4.1 — Backend:** servicio desde `backend/Dockerfile` con `DATABASE_URL`, `DB_AUTO_MIGRATE=true` y `DB_SEED_DEMO=true` (demo).
- [ ] **F4.2 — Secretos:** `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` y `ALLOWED_ORIGINS` con la URL del frontend.
- [ ] **F4.3 — Webhook:** registrar `setWebhook` con la URL pública y el `secret_token`.
- [ ] **F4.4 — Frontend:** servicio desde `frontend/Dockerfile` con `VITE_API_BASE_URL` apuntando al backend.
- [ ] **F4.5 — Humo en producción:** `/api/health` conectado, Test Suite por la API, una factura por Telegram y otra por la web.

**Listo cuando:** el jurado puede abrir la URL pública y probar el agente sin ayuda.

## Fase 5 — Cierre y entrega

- [ ] **F5.1 — Limpieza:** quitar dependencias sin uso (`python-telegram-bot`) y pasar `pytest` a desarrollo.
- [ ] **F5.2 — Congelamiento:** último commit antes de las 09:30 AM del domingo.
- [ ] **F5.3 — README final:** link de la demo desplegada y guía de prueba para el jurado.
- [ ] **F5.4 — Video pitch (3 min):** problema, demo en vivo (Telegram + dashboard) e impacto.
- [ ] **F5.5 — Entrega:** formulario de HackRadar antes de las 11:59 AM.

---

## Después del Demo Day (visión, sin fecha)

Fases candidatas, en orden sugerido, alineadas con la visión de [mission.md](mission.md):

- [ ] **V1 — Canal de correo:** adaptador de entrada de email que reutiliza `ProcessInvoiceUseCase`.
- [ ] **V2 — Tasas en vivo:** `FXRateProvider` con una API de tasas y las fijas como respaldo.
- [ ] **V3 — Tesorería real:** saldo y movimientos leídos desde la cuenta Blinka.
- [ ] **V4 — Multiempresa y roles:** reglas, proveedores y aprobadores por empresa, con autenticación en el dashboard.
- [ ] **V5 — Canal de WhatsApp.**
- [ ] **V6 — Ejecución de pagos vía Blinka:** programar el pago al aprobar, manteniendo el Audit Log.
