# Requisitos — Fase 3: Integración del frontend con la API real

> Rama: `feat/frontend-api-real` · Fase 3 de [roadmap.md](../roadmap.md) (F3.1 a F3.6).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

El dashboard (`frontend/src/App.jsx`) ya intenta leer `GET /api/invoices` y `GET /api/rules`, pero:

- Si la API responde con una lista vacía o falla, muestra en silencio los datos ficticios de `INITIAL_INVOICES`, así que nunca se sabe si lo que se ve es real.
- Aprobar o rechazar en el Drawer solo cambia el estado local: marca `AUTO_APPROVED` (no `HUMAN_APPROVED`), no llama a `POST /api/invoices/{id}/decision` y el texto dice "en Telegram", lo que contradice el principio 4 de la misión (la aprobación ocurre **solo en el dashboard**).
- No existe la subida de facturas desde la web, aunque `POST /api/invoices/upload` ya está listo con `Idempotency-Key` (Fase 2).
- Guardar reglas hace `fetch` sin revisar la respuesta: un `422` se pierde y el panel muestra valores que el backend no aceptó.
- Los badges, filtros y métricas solo conocen tres estados; `HUMAN_APPROVED` y `HUMAN_REJECTED` no se ven.

El backend no cambia en esta fase: todos los endpoints existen.

## Alcance

**Entra (F3.1 a F3.6 completas):**
- Un cliente API pequeño (`frontend/src/api.js`) con `fetch`, que centraliza `VITE_API_BASE_URL`, el manejo de errores (lee `detail` de FastAPI) y los códigos `200`/`201`/`409`/`422`.
- Audit Log con datos reales al abrir la página y un botón **Actualizar**; el Drawer muestra `evaluations` capa por capa (estado, alertas y razón).
- Badges, filtros y métricas para `HUMAN_APPROVED` y `HUMAN_REJECTED`; la autonomía cuenta solo `AUTO_APPROVED` + `REJECTED`.
- Decisión humana real desde el Drawer, con nota opcional y manejo del `409`.
- Botón de subida de facturas (JPG, PNG, WEBP, PDF, 10 MB) con `Idempotency-Key`, estado de procesamiento y resultado.
- Panel de reglas que persiste y muestra los errores de validación.
- Banner de "modo demostración" cuando la API no responde.
- Actualizar `frontend/README.md` y marcar F3.x en el roadmap.

**No entra:**
- Cambios en el backend (endpoints, esquemas o reglas).
- Autenticación o roles de aprobador (es V4 de la visión).
- Actualización automática (polling, WebSocket o SSE).
- Framework de pruebas en el frontend (Vitest, Testing Library).
- Rediseño visual: se reutilizan los componentes y tokens de [DESIGN.md](../../docs/diseno/DESIGN.md).
- Despliegue en Railway (Fase 4).

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **Respaldo de demo con aviso.** Si `GET /api/invoices` falla (red, sin `VITE_API_BASE_URL` o respuesta no `ok`), se muestran los datos de `INITIAL_INVOICES` con un banner visible de "Modo demostración: la API no responde". Si la API responde, se muestran **siempre** los datos reales, aunque la lista esté vacía (con un estado vacío). | Elegido por el equipo. La demo no se rompe si el backend cae, pero nunca se confunden datos ficticios con reales (criterio de viabilidad de la misión). |
| D2 | **En modo demostración no hay escrituras.** Subir, decidir y guardar reglas se deshabilitan con un texto que explica por qué. | Evita que la UI finja un resultado que no quedó en el Audit Log. |
| D3 | **`decided_by` fijo:** constante `DECIDED_BY = 'CFO Demo'` en el frontend. El Drawer solo pide la nota (opcional, máx. 1000 caracteres). | Elegido por el equipo. Sin autenticación en el MVP; el backend exige el campo (1 a 100 caracteres). |
| D4 | **Refresco:** el listado se carga al abrir la página y con un botón **Actualizar** en el Audit Log. Sin polling. Tras una subida o una decisión propia, la factura devuelta por la API reemplaza (o se agrega a) la lista local sin recargar todo. | Elegido por el equipo: simple y suficiente para la demo (llega por Telegram → clic en Actualizar). |
| D5 | **Decisión humana:** `POST /api/invoices/{id}/decision` con `{decision: "APPROVE" \| "REJECT", decided_by, note}`. La respuesta reemplaza la factura en la lista y en el Drawer. Ante `409` (ya decidida o no está en `SCALED_TO_HUMAN`), se muestra el `detail` y se recarga el listado para ver el estado vigente. Los botones se deshabilitan mientras la solicitud está en curso. | La API es la fuente de verdad; el `409` significa que otra persona o pestaña ya decidió. |
| D6 | **Subida con `Idempotency-Key`:** al elegir un archivo se genera `crypto.randomUUID()` y se guarda junto al archivo en el estado del componente. "Reintentar" reusa la misma clave; elegir otro archivo genera una nueva. `201` y `200` se tratan igual (se muestra la factura y su dictamen). Ante `409` se reintenta automáticamente con la misma clave hasta 3 veces, con 2 s de espera, y luego se ofrece "Reintentar". `413`, `415` y `400` muestran el `detail`. El botón se deshabilita mientras se procesa. | Cierra F3.5 con lo que la Fase 2 ya garantiza en el backend: un doble clic o un reintento de red nunca crea una segunda factura. |
| D7 | **Validación previa en el navegador:** tipo (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`) y tamaño (≤ 10 MB) antes de enviar. El backend sigue siendo quien decide. | Respuesta inmediata al usuario sin gastar una llamada a Gemini. |
| D8 | **Reglas:** `POST /api/rules` con los cuatro campos; el estado local solo se actualiza con la respuesta `200`. Un `422` muestra los mensajes de `detail` (por campo cuando `loc` lo indique) y conserva lo que el usuario escribió. | Hoy el panel puede mostrar valores que el backend rechazó. |
| D9 | **Estados y colores:** `HUMAN_APPROVED` y `HUMAN_REJECTED` tienen badge propio (variante del aprobado/rechazado con ícono de persona) y muestran quién y cuándo (`decided_by`, `decided_at`) y la nota. La métrica de autonomía es `(AUTO_APPROVED + REJECTED) / total`. | Misión: las decisiones `HUMAN_*` no cuentan como autónomas y deben quedar trazadas. |
| D10 | **Evaluaciones capa por capa:** el Drawer recorre `evaluations` en el orden de la tubería (`compliance_check`, `integrity_check`, `solvency_check`, `hitl_check`), con su `status` (incluidos `SKIPPED` y `NOT_EVALUATED`), las alertas (código + explicación) y la `reason` si existe. Si `evaluations` viene vacío (datos de demo), se muestra solo `audit_explanation`. | Principio 3 de la misión: explicabilidad total sin leer código. |
| D11 | **Sin dependencias nuevas.** `fetch` nativo y `crypto.randomUUID()`; nada de axios, React Query ni librerías de formularios. | Pragmatismo de hackathon; el stack de [tech-stack.md](../tech-stack.md) no cambia. |

## Contrato de la API usado

| Endpoint | Uso | Respuestas relevantes |
| :--- | :--- | :--- |
| `GET /api/invoices` | Listado del Audit Log | `200` con `InvoiceResponse[]` |
| `POST /api/invoices/upload` | Subida web (`multipart`, campo `file`, header `Idempotency-Key`) | `201` nueva, `200` repetida, `409` en proceso, `413`/`415`/`400` |
| `POST /api/invoices/{id}/decision` | Aprobación o rechazo humano | `200` con la factura, `409` si no está escalada, `422` |
| `GET /api/rules` / `POST /api/rules` | Panel de reglas | `200`, `422` con `detail[]` |

## Restricciones

- Una sola variable de entorno: `VITE_API_BASE_URL` (en el `.env` de la raíz). Ninguna nueva.
- Textos de la UI en español.
- Ningún texto de la UI dice que la aprobación ocurre en Telegram.
- El build de producción (`npm run build`) no debe tener errores ni advertencias nuevas.
