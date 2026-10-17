# Validación — Fase 3: Integración del frontend con la API real

> La rama `feat/frontend-api-real` se puede mergear cuando se cumplen **todos** los criterios bloqueantes.
> Criterio del roadmap: se puede recorrer TC-01 a TC-06 y aprobar un escalamiento solo desde el navegador.
> No se agrega framework de pruebas al frontend: la validación es el build más un recorrido manual contra la API real.

## Criterios bloqueantes

### Build

- [ ] `npm run build` en `frontend/` termina sin errores.
- [ ] `package.json` no tiene dependencias nuevas.
- [ ] `pytest` en `backend/` sigue verde (el backend no cambia).

### Recorrido manual (backend + PostgreSQL con seed en Docker, frontend con `npm run dev`)

**Listado y modo demostración (F3.1)**
- [ ] Al abrir la página, el Audit Log muestra las facturas de `GET /api/invoices` (no las de `INITIAL_INVOICES`) y no aparece el banner de demostración.
- [ ] Con una base sin facturas, se ve el estado vacío, no los datos ficticios.
- [ ] Con el backend apagado, aparecen los datos de demo con el banner "Modo demostración" y los botones de subir, decidir y guardar reglas están deshabilitados.
- [ ] El botón **Actualizar** trae una factura creada por fuera (por `curl` o Telegram) sin recargar la página.
- [ ] El Drawer muestra las cuatro capas de `evaluations` con su estado, alertas (código + explicación) y la razón de `SKIPPED` cuando SARLAFT está desactivado.

**Test Suite TC-01 a TC-06**
- [ ] Cargando cada caso (por subida o por `POST /api/invoices` y luego Actualizar), el dashboard muestra el estado esperado y la regla disparada de cada uno, según [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md).

**Estados humanos y métricas (F3.2)**
- [ ] Hay badge y filtro para `HUMAN_APPROVED` y `HUMAN_REJECTED`, y los contadores suman el total.
- [ ] La autonomía es `(AUTO_APPROVED + REJECTED) / total`: aprobar a mano un escalamiento **no** la sube.

**Decisión humana (F3.3)**
- [ ] Aprobar una factura `SCALED_TO_HUMAN` con nota → pasa a `HUMAN_APPROVED`; el Drawer muestra "CFO Demo", la hora y la nota; tras **Actualizar** el estado persiste.
- [ ] Rechazar otra → `HUMAN_REJECTED` con los mismos datos.
- [ ] Decidir la misma factura desde una segunda pestaña (con la vista vieja) → se muestra el mensaje del `409` y la lista se actualiza al estado vigente.
- [ ] Ningún texto de la UI dice que la aprobación ocurre en Telegram.

**Subida e Idempotency-Key (F3.4 + F3.5)**
- [ ] Subir `backend/tests/fixtures/factura_devstudio.png` muestra "procesando" con el botón deshabilitado y luego la factura con su dictamen; aparece al inicio del Audit Log.
- [ ] En la pestaña Network, la solicitud lleva el header `Idempotency-Key` con un UUID.
- [ ] "Reintentar" (o repetir la solicitud con la misma clave desde DevTools) devuelve `200` con el mismo `id` y no crea una segunda fila tras **Actualizar**.
- [ ] Elegir el mismo archivo otra vez (clave nueva) crea una factura nueva que queda `REJECTED` por INTEG-01, como define la Fase 2.
- [ ] Un archivo `.txt` o de más de 10 MB se rechaza en el navegador sin llamar a la API.

**Reglas (F3.6)**
- [ ] Cambiar `max_autonomous_usd` y guardar → mensaje "Reglas guardadas"; tras recargar la página el valor persiste.
- [ ] `duplicate_check_days = 0` (o 400) → el `422` se muestra junto al campo y el panel conserva lo escrito sin cambiar las reglas vigentes.

### Código

- [ ] Todas las llamadas HTTP pasan por `frontend/src/api.js`; ningún componente usa `fetch` directo.
- [ ] La única variable de entorno sigue siendo `VITE_API_BASE_URL`.
- [ ] Un solo mapa de estados compartido por la tabla, el Drawer y las métricas.

### Documentación

- [ ] `frontend/README.md` describe el modo demostración, el botón Actualizar, la subida con `Idempotency-Key` y la decisión humana.
- [ ] `specs/roadmap.md` tiene F3.1 a F3.6 marcadas.

## Verificación recomendada (no bloquea el merge)

- [ ] Enviar una factura por Telegram, pulsar **Actualizar** y aprobarla desde el Drawer; confirmar que el chat recibe el aviso de la decisión.
- [ ] Revisar el dashboard en un ancho de 375 px (Drawer, subida y tabla usables).
- [ ] Build de producción con `frontend/Dockerfile` apuntando al backend local.

## Cómo correr

Backend + PostgreSQL con seed: ver [backend/README.md](../../backend/README.md) (PostgreSQL 16 en Docker, `DB_AUTO_MIGRATE=true`, `DB_SEED_DEMO=true`, `uvicorn` en el puerto 8000). Luego, con `VITE_API_BASE_URL=http://localhost:8000` en el `.env` de la raíz:

```bash
cd frontend && npm install && npm run dev
```

```bash
cd frontend && npm run build
```
