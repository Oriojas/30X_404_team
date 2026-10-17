# Validación — Fase 4: Despliegue en Railway

> La rama `feat/despliegue-railway` se puede mergear cuando se cumplen **todos** los criterios bloqueantes.
> Criterio del roadmap: el jurado puede abrir la URL pública y probar el agente sin ayuda.
> La validación combina pruebas locales de las imágenes, el script de humo contra producción y un recorrido manual desde la URL pública.

## Criterios bloqueantes

> Avance al 17-oct-2026: la rama ya está en `master` (#12), el frontend público consume el backend real y el recorrido web (subida, aprobación y reglas) pasó en producción. Falta el reenvío por Telegram.

### Código y build (local)

- [x] `pytest` en `backend/` verde, incluida la prueba nueva de `registrar_webhook.py`. *(68 pasadas, 6 omitidas sin `TEST_DATABASE_URL`)*
- [x] `npm run build` en `frontend/` sin errores.
- [x] `docker build` del backend y del frontend terminan sin errores; el contexto del frontend no incluye `node_modules` ni `dist`. *(con `.dockerignore` en ambos)*
- [x] La imagen del frontend construida con `--build-arg VITE_API_BASE_URL=http://localhost:8000` muestra datos reales del backend local, sin banner de "Modo demostración". *(se probó con `http://localhost:8001`: el dashboard mostró las facturas del seed, sin banner y sin errores en consola)*
- [x] `nginx.conf.template` ya no tiene el bloque `/api/` y el contenedor arranca en el `$PORT` recibido. *(arrancó en `PORT=8080`)*
- [x] La imagen del backend responde `GET /api/health` con `status: ok` y la base conectada.
- [x] `humo_produccion.py` contra el backend local con seed da los seis casos en verde **dos veces seguidas** (la segunda corrida devuelve `200` con las mismas facturas, sin duplicados INTEG-01 nuevos). *(9/9 en ambas corridas)*
- [x] Ningún archivo versionado contiene tokens, claves ni `DATABASE_URL` reales. *(búsqueda con `git grep` de claves `AIza…`, tokens de bot, hex de 64 y URLs de Postgres de Railway: sin resultados)*

### Despliegue en Railway

- [x] Tres servicios en un canvas: PostgreSQL, `backend` y `frontend`, creados o actualizados por `railway config apply` desde `.railway/railway.ts` (builder Dockerfile, healthcheck y reinicio visibles en *Settings*). *(el frontend es el servicio existente `30X_404_team`)*
- [x] `railway config plan` después del apply no muestra diferencias (sin drift entre el archivo y Railway). *("already up to date", también después de cargar los secretos)*
- [x] `.railway/railway.ts` está versionado y no contiene valores de secretos (solo `preserve()`).
- [x] El deploy del backend pasa el healthcheck `/api/health`.
- [x] `ALLOWED_ORIGINS` contiene exactamente el dominio `https` del frontend (no `*`). *(`https://30x404team-production.up.railway.app`)*
- [x] `getWebhookInfo` (vía `registrar_webhook.py --info`) muestra la URL pública del backend, `pending_update_count` en 0 y sin `last_error_message`. *(URL `…/api/webhook/telegram`, 0 pendientes, sin error; sin el secreto el webhook responde `401`)*

### Humo en producción (F4.5)

- [x] `python backend/scripts/humo_produccion.py https://<backend>.up.railway.app --origen https://<frontend>.up.railway.app` termina con código 0: *(9/9 contra `https://backend-production-ea088.up.railway.app`)*

  | Caso | Factura | Estado esperado | Regla esperada |
  | :--- | :--- | :--- | :--- |
  | TC-01 | AWS-2026-10 | `AUTO_APPROVED` | — |
  | TC-02 | DS-1042 | `REJECTED` | `INTEG-01` |
  | TC-03 | DC-001 | `SCALED_TO_HUMAN` | `HITL-02` |
  | TC-04 | NA-090 | `SCALED_TO_HUMAN` | `HITL-01` |
  | TC-05 | LEM-3400 | `SCALED_TO_HUMAN` | `FIN-01` |
  | TC-06 | GTP-01 | `REJECTED` | `COMP-01` |

- [x] El preflight CORS desde el origen del frontend responde con `access-control-allow-origin` igual a ese origen.

### Recorrido manual desde la URL pública

> En un navegador o ventana privada, sin backend local corriendo.

- [x] La URL pública del frontend abre el dashboard **sin** banner de "Modo demostración" y el Audit Log muestra las facturas del seed y las del humo. *(17-oct-2026, tras el merge de #12: el bundle apunta a `https://backend-production-ea088.up.railway.app` y el Audit Log lista 12 facturas)*
- [x] La consola del navegador no muestra errores de CORS ni de contenido mixto (`http` en página `https`). *(consola vacía; `/api/invoices` y `/api/rules` por https)*
- [x] **Web:** subir una factura real (imagen o PDF) desde el dashboard produce un dictamen con datos extraídos por Gemini (no una extracción vacía con confianza 0). *(`factura_devstudio.png`: Gemini leyó `DS-2026-1107`, 4.200.000 COP → 1.000 USD, `AUTO_APPROVED`; id 13, canal `WEB`)*
- [x] **Telegram, aviso:** enviar una factura real al bot devuelve el aviso del dictamen en el chat. *(Factura `#00042-1`: Gemini leyó 205,00 con confianza 0,8 y moneda ambigua `XXX`, y se escaló por INTEG-04, INTEG-03, HITL-02 y HITL-03, como manda la tolerancia cero. Quedó con id 12 en `GET /api/invoices`.)*
- [x] **Telegram, dashboard:** tras **Actualizar**, esa factura aparece en el Audit Log del dashboard público. *(`#00042-1` visible como `SCALED_TO_HUMAN`)*
- [ ] **Telegram, reintento:** reenviar el mismo archivo no crea otra factura procesada (INTEG-01 por hash) y no llega un aviso duplicado del mismo update.
- [x] **Aprobación:** abrir un `SCALED_TO_HUMAN` en el Drawer, aprobarlo con una nota y ver `HUMAN_APPROVED` con `decided_by` y fecha; recargar la página y el estado persiste. *(`NA-090`, id 9: `CFO Demo`, 2026-10-17 10:45 UTC, con nota; persiste tras recargar. El humo acepta `HUMAN_*` en los casos que escalan)*
- [x] **Reglas:** cambiar un umbral, guardar, recargar y ver el valor persistido. *(ventana de duplicados 30 → 45 días, persistió tras recargar y se restauró a 30)*

### Documentación

- [x] `backend/README.md` y `frontend/README.md` describen el despliegue (orden, `railway config plan`/`apply`, secretos, variables, scripts) de forma que otra persona del equipo pueda repetirlo.
- [x] `.env.example` documenta `TELEGRAM_WEBHOOK_URL` y el formato de `ALLOWED_ORIGINS` para producción.
- [ ] F4.1 a F4.5 marcadas en [roadmap.md](../roadmap.md) con fecha; Railway "En uso" en [tech-stack.md](../tech-stack.md).

## No bloqueantes

- Tiempo de arranque en frío del backend anotado (para el pitch).
- Captura del dashboard en producción para el README final (Fase 5).
