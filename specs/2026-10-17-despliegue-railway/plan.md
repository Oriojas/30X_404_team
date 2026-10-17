# Plan — Fase 4: Despliegue en Railway

> Rama: `feat/despliegue-railway`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).
> Cada grupo se puede terminar, probar y commitear por separado. Los grupos 1 a 4 son código; 5 a 7 son el despliegue real y el cierre.

## 1. Imagen del frontend lista para Railway (F4.4)

> Hecho: `948999d`.

1.1. En `frontend/Dockerfile`, declarar `ARG VITE_API_BASE_URL` y `ENV VITE_API_BASE_URL=$VITE_API_BASE_URL` en la etapa `builder`, antes de `npm run build`; cambiar `npm install` por `npm ci` (D4).
1.2. En `frontend/nginx.conf.template`, quitar el bloque `location /api/` y su resolver; dejar solo el estático con `try_files` y `listen ${PORT}` (D1).
1.3. Crear `frontend/.dockerignore` (`node_modules`, `dist`, `.env*`).
1.4. Probar en local: `docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t paybot-frontend frontend` y `docker run -e PORT=8080 -p 8080:8080 paybot-frontend`; el dashboard carga datos reales del backend local (sin banner de demostración).

## 2. Imagen del backend e infraestructura como código (F4.1)

> Hecho: `eebf0ff`, `6fc1f5e`.

2.1. Crear `backend/.dockerignore` (`__pycache__`, `tests`, `.pytest_cache`, `scripts/__pycache__`, `.env*`).
2.2. ~~Instalar Railway CLI (`brew install railway`), `railway config init` y SDK `railway@3.16.0` en el `package.json` de la raíz~~ *(hecho el 17-oct-2026, CLI 5.70.0)*.
2.3. `.railway/railway.ts` con `Postgres`, `backend` y `30X_404_team` (frontend): root, builder `DOCKERFILE`, `watchPatterns`, healthcheck, `ON_FAILURE` con 5 reintentos y variables de D3/D4 (D2). *(Borrador hecho; evalúa sin errores con Node.)*
2.4. Quitar `.railway/` de `.gitignore` e ignorar solo los planes (`railway-plan*.json`).
2.5. Probar en local: `docker build -t paybot-backend backend` y correrlo con `DATABASE_URL` hacia el PostgreSQL 16 de Docker, `DB_SEED_DEMO=true` y `PORT=8001`; `GET /api/health` responde `ok` con la base conectada.

## 3. Registro del webhook de Telegram (F4.3)

> Hecho: `9f2bd6d`; webhook registrado en producción.

3.1. Agregar `telegram_webhook_url: str | None = None` a `Settings` en `backend/app/config.py`.
3.2. Crear `backend/scripts/registrar_webhook.py`: valida que existan token, URL (`https://…/api/webhook/telegram`) y secreto; llama `setWebhook` con `url`, `secret_token`, `allowed_updates=["message"]` y `drop_pending_updates=true`; imprime `getWebhookInfo` (url, pendientes, último error) sin mostrar el token (D6).
3.3. Opción `--info` para solo consultar el estado y `--borrar` para `deleteWebhook` (útil al volver a local).
3.4. Prueba unitaria con `httpx.MockTransport`: arma la llamada correcta y falla con mensaje claro si falta una variable.

## 4. Script de humo (F4.5)

> Hecho: `9a0e1ea`; 9/9 en local (dos corridas) y en producción.

4.1. Crear `backend/scripts/humo_produccion.py <URL_BASE>` con `httpx` síncrono.
4.2. Paso 1: `GET /api/health` → `status == "ok"` y base conectada.
4.3. Paso 2: TC-01 a TC-06 por `POST /api/invoices` con `Idempotency-Key: humo-tc-0N` y los payloads de `test_postgres_integration.py`; aceptar `201` o `200` (D7).
4.4. Comparar `decision_status` y la regla esperada en `audit_explanation`; imprimir una tabla caso / esperado / obtenido / ✅❌ y salir con código 1 si alguno falla.
4.5. Paso 3: `GET /api/rules` responde `200`; y un preflight `OPTIONS /api/invoices` con `Origin: <URL_FRONTEND>` (argumento opcional `--origen`) devuelve `access-control-allow-origin` con ese origen.
4.6. Correrlo contra el backend local con seed: todo en verde, y una segunda corrida también (idempotencia).

## 5. Documentación y variables

5.1. `.env.example`: comentar qué variables van a cada servicio de Railway y el formato exacto de `ALLOWED_ORIGINS` y `TELEGRAM_WEBHOOK_URL`.
5.2. `backend/README.md`: sección "Despliegue en Railway" con el orden de D5, la tabla de variables de D3, cómo usar `railway config plan` / `apply` y cargar los secretos y cómo correr `registrar_webhook.py` y `humo_produccion.py`.
5.3. `frontend/README.md`: `VITE_API_BASE_URL` como build arg, que cambiarla exige redeploy, y que ya no hay proxy `/api/`.
5.4. `pytest` en `backend/` sigue verde y `npm run build` en `frontend/` sin errores.

## 6. Despliegue real (con el Railway CLI)

6.1. Resolver "Could not load branches" (permisos de la app de GitHub de Railway sobre `Oriojas/30X_404_team`): sin eso no se puede crear el servicio `backend` desde el repo.
6.2. El equipo inicia sesión: `railway login` y `railway link` (proyecto `30X_404_team`, entorno `production`). Confirmar con `railway status` que el nombre del proyecto coincide con el de `railway.ts`.
6.3. `railway config plan`: debe **crear** `Postgres` y `backend` y solo **actualizar** `30X_404_team`, sin destruir nada. Si propone borrar o recrear el frontend, ajustar el archivo antes de seguir.
6.4. `railway config apply`.
> *Avance del 17-oct-2026:* 6.2 a 6.4 hechos y dominio del backend generado (`https://backend-production-ea088.up.railway.app`). El backend está en línea con `GET /api/health` → `connected`, el seed cargado y CORS respondiendo al dominio del frontend. `railway config plan` ya no muestra diferencias. `restartPolicyType` no se declara porque `ON_FAILURE` es el valor por defecto y declararlo dejaba drift permanente.

> 6.5 a 6.7 hechos: el equipo cargó el bot token y la clave de Gemini, el secreto del webhook se generó al azar y el webhook quedó registrado. Falta 6.1 (sin bloquear: el backend se creó igual).

6.5. Cargar los secretos del backend (lo hace el equipo, sin pegarlos en el chat): `railway variables --service backend --set GEMINI_API_KEY=…` y lo mismo con `TELEGRAM_BOT_TOKEN` y `TELEGRAM_WEBHOOK_SECRET`.
6.6. `railway domain --service backend` para generar el dominio público; redeploy de `backend` y de `30X_404_team` (este último para que Vite tome `VITE_API_BASE_URL`). Debe hacerse antes de mergear a `master`, que hace auto-deploy.
6.7. Desde local con las variables de producción: `python backend/scripts/registrar_webhook.py` y verificar `getWebhookInfo` sin errores.

## 7. Humo, validación y cierre

7.1. `python backend/scripts/humo_produccion.py https://<backend>.up.railway.app --origen https://30x404team-production.up.railway.app` en verde.
7.2. Recorrer el checklist manual de [validation.md](validation.md) (Telegram, subida web, aprobación desde el navegador público).
7.3. Marcar F4.1 a F4.5 en [roadmap.md](../roadmap.md) con fecha y resultado; en [tech-stack.md](../tech-stack.md), Railway "En uso" y la conexión por URL pública + CORS.
7.4. Actualizar los enlaces del README raíz si el dominio cambió.
