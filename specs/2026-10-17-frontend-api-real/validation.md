# Validación — Fase 3: Integración del frontend con la API real

> La rama `feat/frontend-api-real` se puede mergear cuando se cumplen **todos** los criterios bloqueantes.
> Criterio del roadmap: se puede recorrer TC-01 a TC-06 y aprobar un escalamiento solo desde el navegador.
> No se agrega framework de pruebas al frontend: la validación es el build más un recorrido manual contra la API real.

## Criterios bloqueantes

> Verificado el 17-oct-2026 en `feat/frontend-api-real`: `npm run build` sin errores; `pytest` 64 pasadas (6 omitidas sin `TEST_DATABASE_URL`); recorrido en el navegador del Browser pane contra el backend con PostgreSQL 16 en Docker (con y sin seed) y Gemini real para las subidas.

### Build

- [x] `npm run build` en `frontend/` termina sin errores.
- [x] `package.json` no tiene dependencias nuevas.
- [x] `pytest` en `backend/` sigue verde (el backend no cambia).

### Recorrido manual (backend + PostgreSQL con seed en Docker, frontend con `npm run dev`)

**Listado y modo demostración (F3.1)**
- [x] Al abrir la página, el Audit Log muestra las facturas de `GET /api/invoices` (no las de `INITIAL_INVOICES`) y no aparece el banner de demostración.
- [x] Con una base sin facturas, se ve el estado vacío, no los datos ficticios.
- [x] Con el backend apagado, aparecen los datos de demo con el banner "Modo demostración" y los botones de subir, decidir y guardar reglas están deshabilitados.
- [x] El botón **Actualizar** trae una factura creada por fuera (por `curl` o Telegram) sin recargar la página.
- [x] El Drawer muestra las cuatro capas de `evaluations` con su estado, alertas (código + explicación) y la razón de `SKIPPED` cuando SARLAFT está desactivado.

**Test Suite TC-01 a TC-06**
- [x] Cargando cada caso (por subida o por `POST /api/invoices` y luego Actualizar), el dashboard muestra el estado esperado y la regla disparada de cada uno, según [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md).

  | Caso | Factura | Estado en el dashboard | Reglas en el Drawer |
  | :--- | :--- | :--- | :--- |
  | TC-01 | AWS-2026-10 | `AUTO_APPROVED` | 4 capas aprobadas |
  | TC-02 | DS-1042 | `REJECTED` | `INTEG-01`; Solvencia y HITL no evaluadas |
  | TC-03 | DC-001 | `SCALED_TO_HUMAN` | `HITL-02` |
  | TC-04 | NA-090 | `SCALED_TO_HUMAN` | `HITL-01` |
  | TC-05 | LEM-3400 | `SCALED_TO_HUMAN` | `FIN-01`, `HITL-01` |
  | TC-06 | GTP-01 | `REJECTED` | `COMP-01`; resto no evaluadas |

**Estados humanos y métricas (F3.2)**
- [x] Hay badge y filtro para `HUMAN_APPROVED` y `HUMAN_REJECTED`, y los contadores suman el total.
- [x] La autonomía es `(AUTO_APPROVED + REJECTED) / total`: aprobar a mano un escalamiento **no** la sube.

**Decisión humana (F3.3)**
- [x] Aprobar una factura `SCALED_TO_HUMAN` con nota → pasa a `HUMAN_APPROVED`; el Drawer muestra "CFO Demo", la hora y la nota; tras **Actualizar** el estado persiste.
- [x] Rechazar otra → `HUMAN_REJECTED` con los mismos datos.
- [x] Decidir la misma factura desde una segunda pestaña (con la vista vieja) → se muestra el mensaje del `409` y la lista se actualiza al estado vigente.
- [x] Ningún texto de la UI dice que la aprobación ocurre en Telegram.

**Subida e Idempotency-Key (F3.4 + F3.5)**
- [x] Subir `backend/tests/fixtures/factura_devstudio.png` muestra "procesando" con el botón deshabilitado y luego la factura con su dictamen; aparece al inicio del Audit Log.
- [x] En la pestaña Network, la solicitud lleva el header `Idempotency-Key` con un UUID.
- [x] "Reintentar" (o repetir la solicitud con la misma clave desde DevTools) devuelve `200` con el mismo `id` y no crea una segunda fila tras **Actualizar**. *(Verificado repitiendo la clave con `curl`: tras un `201` la UI no ofrece "Reintentar".)*
- [x] Un `409` en la subida se reintenta solo con la misma clave cada 2 s (simulado con dos `409` antes del `201`).
- [x] Elegir el mismo archivo otra vez (clave nueva) crea una factura nueva que queda `REJECTED` por INTEG-01, como define la Fase 2.
- [x] Un archivo `.txt` o de más de 10 MB se rechaza en el navegador sin llamar a la API.

**Reglas (F3.6)**
- [x] Cambiar `max_autonomous_usd` y guardar → mensaje "Reglas guardadas"; tras recargar la página el valor persiste.
- [x] `duplicate_check_days = 0` (o 400) → el `422` se muestra junto al campo y el panel conserva lo escrito sin cambiar las reglas vigentes. *(Para que el `422` sea alcanzable, la ventana de duplicados y la reserva de tesorería pasaron a ser campos numéricos.)*

### Código

- [x] Todas las llamadas HTTP pasan por `frontend/src/api.js`; ningún componente usa `fetch` directo.
- [x] La única variable de entorno sigue siendo `VITE_API_BASE_URL`.
- [x] Un solo mapa de estados compartido por la tabla, el Drawer y las métricas.

### Documentación

- [x] `frontend/README.md` describe el modo demostración, el botón Actualizar, la subida con `Idempotency-Key` y la decisión humana.
- [x] `specs/roadmap.md` tiene F3.1 a F3.6 marcadas.

## Verificación recomendada (no bloquea el merge)

- [ ] Enviar una factura por Telegram, pulsar **Actualizar** y aprobarla desde el Drawer; confirmar que el chat recibe el aviso de la decisión.
- [x] Revisar el dashboard en un ancho de 375 px (Drawer, subida y tabla usables). *(Sin scroll horizontal de la página; la tabla y los filtros se desplazan dentro de su contenedor.)*
- [ ] Build de producción con `frontend/Dockerfile` apuntando al backend local.

## Hallazgos y riesgos aceptados

- **Mensajes del `422` en inglés:** son los de Pydantic por defecto (p. ej. "Input should be less than or equal to 365"). Se muestran tal cual.
- **Seed:** la factura `HUMAN_APPROVED` del seed (LEM-3301) no tiene `decided_by`; el Drawer muestra "Sin registrar". Las decisiones hechas desde el dashboard sí lo guardan.
- **`vite.config.js` no leía el `.env` de la raíz:** se agregó `envDir: '..'`; sin él, el dashboard local quedaba siempre en modo demostración.
- **Despliegue (F4.4):** `frontend/Dockerfile` no declara `ARG VITE_API_BASE_URL`, así que el build en Railway no recibirá la URL hasta agregarlo.
- **Pendiente de la verificación recomendada:** el flujo por Telegram y el build con `frontend/Dockerfile` no se probaron en esta fase.

## Cómo correr

Backend + PostgreSQL con seed: ver [backend/README.md](../../backend/README.md) (PostgreSQL 16 en Docker, `DB_AUTO_MIGRATE=true`, `DB_SEED_DEMO=true`, `uvicorn` en el puerto 8000). Luego, con `VITE_API_BASE_URL=http://localhost:8000` en el `.env` de la raíz:

```bash
cd frontend && npm install && npm run dev
```

```bash
cd frontend && npm run build
```
