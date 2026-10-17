# Requisitos — Fase 4: Despliegue en Railway

> Rama: `feat/despliegue-railway` (sale de `feat/frontend-api-real`, mergeada en `master` con el PR #11) · Fase 4 de [roadmap.md](../roadmap.md) (F4.1 a F4.5).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

Las fases 1 a 3 dejaron el agente completo en local: OCR real con Gemini, ingesta idempotente y dashboard conectado a la API. Falta lo que pide el criterio de **viabilidad** de la misión: una demo pública en Railway que el jurado pueda probar sin ayuda, con el repositorio respaldando exactamente lo que se muestra.

Hoy hay obstáculos concretos para desplegar:

- `frontend/Dockerfile` no declara `ARG VITE_API_BASE_URL`, así que Vite construye sin URL del backend y el dashboard cae en **modo demostración**.
- `frontend/nginx.conf.template` proxya `/api/` a `http://backend:8000` con el resolver de Docker (`127.0.0.11`), que no existe en Railway.
- No hay `.dockerignore`: el contexto del frontend sube `node_modules` y `dist`.
- `TELEGRAM_WEBHOOK_URL` está en `.env.example` pero no en `Settings`, y no hay forma versionada de llamar `setWebhook`.
- No hay configuración versionada para Railway (builder, healthcheck, reinicio). Además, Railway deprecó *Config as Code* (`railway.json`/`railway.toml`): desde el 28-ago-2026 los servicios que nunca lo usaron no pueden activarlo, y deja de funcionar el 1-dic-2026. Lo reemplaza *Infrastructure as Code* (`.railway/railway.ts`), que se aplica con el Railway CLI.
- Ya existe un servicio de frontend publicado en `https://30x404team-production.up.railway.app` (README); se reutiliza ese servicio y su dominio.

**Estado verificado el 17-oct-2026 (09:43, desde fuera de Railway):**

- El frontend publicado ya trae el código de la Fase 3 (el bundle incluye el banner de "Modo demostración", la subida y la decisión humana); `index.html` es de las 09:35 del mismo día.
- El bundle **no** tiene ninguna URL de backend: se construyó sin `VITE_API_BASE_URL`, así que llama rutas relativas `/api/...`.
- `GET /api/health` y `GET /api/invoices` sobre el dominio del frontend se quedan colgadas más de 15 s sin respuesta: nginx intenta el proxy a `backend:8000` con un resolver que no existe en Railway. El dashboard termina en modo demostración después de esa espera.
- No hay en el repo `railway.json`, `railway.toml`, `nixpacks.toml`, `Procfile` ni `.dockerignore`, y el historial solo tiene el commit `e178b8f` (resolver dinámico en nginx). La configuración que exista vive solo en el dashboard.
- El canvas de Railway (captura del dashboard) tiene **un solo servicio**, `30X_404_team`: repo `Oriojas/30X_404_team`, root `/frontend`, rama `master` con auto-deploy. **No hay backend ni PostgreSQL.** El deploy de las 09:35 coincide con el merge del PR #11 (Fase 3) en `master`.
- El dashboard de Railway muestra "Could not load branches", es decir, falla al listar las ramas. Lo más probable es que la app de GitHub de Railway no tenga permisos sobre el repo. Hay que revisarlo antes de crear el servicio del backend.
- Como `master` hace auto-deploy, cualquier merge despliega el frontend. Por eso hay que definir `VITE_API_BASE_URL` en Railway **antes** de mergear esta rama.

**Hito fijo:** congelamiento de código el domingo 18-oct-2026 a las 09:30 AM.

## Alcance

**Entra (F4.1 a F4.5):**
- `.railway/railway.ts` (Infrastructure as Code): PostgreSQL, `backend` y el frontend existente, con root, builder Dockerfile, healthcheck, reinicio y variables; SDK `railway` fijado como dependencia de desarrollo en el `package.json` de la raíz. `.railway/` deja de estar en `.gitignore`.
- `frontend/Dockerfile` con `ARG`/`ENV VITE_API_BASE_URL` antes de `npm run build` y `npm ci`.
- `frontend/nginx.conf.template` sin el bloque `/api/`: solo sirve el build estático en `$PORT`.
- `.dockerignore` en `backend/` y `frontend/`.
- `telegram_webhook_url` en `Settings` y script `backend/scripts/registrar_webhook.py`.
- Script de humo `backend/scripts/humo_produccion.py` contra una URL base.
- Guía paso a paso del despliegue (servicios, variables, orden) en `backend/README.md` y `frontend/README.md`, y actualización de `.env.example`.
- Ejecución real del despliegue (la hace el equipo en el dashboard de Railway), recorrido de [validation.md](validation.md) y marcar F4.x en el roadmap.
- `tech-stack.md`: Railway pasa a "En uso" y se documenta la conexión frontend → backend.

**No entra:**
- Cambios en la tubería de reglas, el OCR o los endpoints.
- Proxy por red privada de Railway (descartado, ver D1).
- `railway.json`/`railway.toml` (Config as Code deprecado; ver D2).
- Aplicar la infraestructura desde CI (`railwayapp/config` en GitHub Actions).
- Railway CLI, CI/CD o despliegue desde GitHub Actions.
- Dominio propio, autenticación o rate limiting.
- La limpieza de dependencias (F5.1) y el README final del jurado (F5.3): son de la Fase 5.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **Frontend → backend por URL pública + CORS.** `VITE_API_BASE_URL` = dominio público del backend (`https://<backend>.up.railway.app`), inyectado como build arg. `ALLOWED_ORIGINS` del backend = dominio del frontend (sin `*` en producción). Se elimina el proxy `/api/` de nginx. | Elegido por el equipo. Es lo que ya dice el roadmap y el cliente `api.js` ya funciona así en local; el proxy por red privada exige resolver IPv6 de Railway y más piezas que pueden fallar a pocas horas del congelamiento. |
| D2 | **Infraestructura como código en `.railway/railway.ts`, aplicada con el Railway CLI.** Un solo archivo para todo el proyecto: `Postgres`, `backend` (root `/backend`) y el servicio existente `30X_404_team` (root `/frontend`, se conserva el nombre para que no se borre y recree). `railway config plan` antes de cada `railway config apply`. Los secretos (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`) van con `preserve()` y se cargan en Railway, nunca en el archivo. Los dominios generados de Railway no se declaran: se generan con `railway domain`. | El equipo pidió dejarlo como código. Config as Code (`railway.json`) está deprecado y no se puede activar en servicios que nunca lo usaron. Un `apply` de proyecto completo borra lo que no esté declarado, así que el archivo debe listar todos los recursos. |
| D3 | **Backend:** builder `DOCKERFILE`, `healthcheckPath: /api/health`, `restartPolicyType: ON_FAILURE`. Variables: `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `DB_AUTO_MIGRATE=true`, `DB_SEED_DEMO=true`, `ENVIRONMENT=production`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_WEBHOOK_URL`, `ALLOWED_ORIGINS`. `PORT` lo inyecta Railway. | F4.1 y F4.2. El seed es ficticio y es idempotente, así que reiniciar no duplica datos. |
| D4 | **Frontend:** builder `DOCKERFILE`, healthcheck `/`. Variable `VITE_API_BASE_URL` declarada como `ARG` en el Dockerfile (Railway pasa las variables del servicio como build args solo si están declaradas). Cambiarla exige redeploy. | F4.4. Sin el `ARG`, el build sale sin URL y el dashboard queda en modo demostración. |
| D5 | **Orden de despliegue:** PostgreSQL → backend (genera dominio) → frontend con `VITE_API_BASE_URL` del backend → volver al backend y fijar `ALLOWED_ORIGINS` con el dominio del frontend → registrar el webhook. | Resuelve la dependencia circular de dominios sin adivinar URLs. |
| D6 | **Webhook por script:** `backend/scripts/registrar_webhook.py` lee `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_URL` y `TELEGRAM_WEBHOOK_SECRET` desde `Settings` (se agrega `telegram_webhook_url`), llama `setWebhook` con `secret_token` y `drop_pending_updates=true`, y muestra `getWebhookInfo`. Usa `httpx` (ya es dependencia). Se corre desde local con el `.env` apuntando a producción, o con `railway run`. | Elegido por el equipo. Repetible y sin pegar el token en un `curl` del historial. Respeta la regla de que solo `config.py` lee variables. |
| D7 | **Humo idempotente:** `backend/scripts/humo_produccion.py <URL_BASE>` verifica `/api/health` (`status: ok`, `database` conectada), envía TC-01 a TC-06 por `POST /api/invoices` con un `Idempotency-Key` fijo por caso (`humo-tc-01` … `humo-tc-06`) y compara estado y regla esperados; sale con código ≠ 0 si algo falla. Los payloads son los de `test_postgres_integration.py`. | Elegido por el equipo. La clave fija hace que repetir el humo devuelva las mismas facturas (`200`) en vez de convertirlas en duplicados INTEG-01; reutiliza la garantía de la Fase 2. |
| D8 | **Validación manual en producción:** una factura real por Telegram, otra por la subida web y la aprobación de un escalamiento desde la URL pública, en un navegador sin `.env` local. | El humo prueba la API; esto prueba lo que verá el jurado (F4.5). |
| D9 | **Sin secretos en el repo:** `railway.ts` y la guía solo nombran variables (secretos con `preserve()`); los valores viven en Railway. `.env.example` documenta cada una con un valor de ejemplo. | Regla del proyecto (un solo `.env` en la raíz, nunca versionado). |

## Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| Gemini sin cuota o modelo no disponible en la cuenta de producción. | El adaptador ya falla seguro (INTEG-03 escala). Validar una subida real antes del congelamiento. |
| El backend arranca antes de que PostgreSQL acepte conexiones. | `restartPolicyType: ON_FAILURE`; el healthcheck no da el deploy por bueno hasta que responda. |
| CORS mal configurado (barra final, `http` vs `https`). | La guía fija el formato exacto (`https://dominio`, sin barra) y la validación lo comprueba desde el navegador. |
| Un deploy roto cerca del congelamiento. | Railway permite volver al deploy anterior; el congelamiento es sobre el commit desplegado y probado. |
