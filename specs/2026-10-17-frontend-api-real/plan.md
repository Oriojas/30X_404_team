# Plan — Fase 3: Integración del frontend con la API real

> Rama: `feat/frontend-api-real`. Requisitos en [requirements.md](requirements.md); criterios de cierre en [validation.md](validation.md).
> Cada grupo se puede terminar, probar y commitear por separado.

## 1. Cliente API

1.1. Crear `frontend/src/api.js` con `API_BASE = import.meta.env.VITE_API_BASE_URL || ''` y un `request(path, options)` que devuelva `{ status, data }` y lance un `ApiError(status, message, detail)` cuando la respuesta no sea `ok` (mensaje desde `detail` de FastAPI, sea texto o lista de `422`).
1.2. Funciones: `listInvoices()`, `uploadInvoice(file, idempotencyKey)`, `decideInvoice(id, decision, note)`, `getRules()`, `saveRules(rules)`.
1.3. Constante `DECIDED_BY = 'CFO Demo'` (D3) y la lista de tipos y tamaño máximo de archivo (D7).

## 2. Listado real y modo demostración (F3.1)

2.1. En `App.jsx`, reemplazar el `useEffect` actual por `loadInvoices()` que use el cliente; estados `loading`, `apiAvailable` y `lastError`.
2.2. API disponible → `setInvoices(data)` aunque venga vacía; API caída → `INITIAL_INVOICES` y `apiAvailable = false` (D1).
2.3. Banner de "Modo demostración" (componente pequeño o dentro del Audit Log) y estado vacío en `AuditTable` cuando no hay facturas.
2.4. Botón **Actualizar** en `AuditTable` que llama a `loadInvoices()`, con indicador de carga (D4).
2.5. Ajustar los datos de `INITIAL_INVOICES` para que tengan la misma forma que `InvoiceResponse` (incluido `evaluations`, aunque sea vacío).

## 3. Evaluaciones en el Drawer (F3.1)

3.1. En `AuditDrawer.jsx`, sección "Evaluación por capa" que recorra `evaluations` en el orden de la tubería, con estado, alertas (código + explicación) y `reason` (D10).
3.2. Si `evaluations` está vacío, mostrar solo `audit_explanation`.

## 4. Estados humanos y métricas (F3.2)

4.1. Un mapa único de estados (etiqueta, colores, ícono) compartido por `AuditTable`, `AuditDrawer` y `DashboardMetrics`, con `HUMAN_APPROVED` y `HUMAN_REJECTED` (D9).
4.2. Filtros y contadores de `AuditTable` para los cinco estados.
4.3. Métrica de autonomía `(AUTO_APPROVED + REJECTED) / total` en `DashboardMetrics` (y donde se muestre hoy).
4.4. En el Drawer, para los estados `HUMAN_*`: `decided_by`, `decided_at` formateado y `human_note`.

## 5. Decisión humana real (F3.3)

5.1. Quitar `handleApproveHuman`/`handleRejectHuman` locales y los textos "en Telegram".
5.2. En el Drawer, campo de nota opcional (máx. 1000) y botones Aprobar/Rechazar que llaman a `decideInvoice` con `DECIDED_BY` (D5).
5.3. Respuesta `200` → reemplazar la factura en la lista y en `selectedInvoice`.
5.4. `409` → mostrar el `detail` en el Drawer y llamar a `loadInvoices()`; otros errores → mensaje y botones habilitados de nuevo.
5.5. Deshabilitar los botones mientras se envía y en modo demostración (D2).

## 6. Subida de facturas con Idempotency-Key (F3.4 + F3.5)

6.1. Componente `InvoiceUpload.jsx` (ubicado junto al Audit Log) con input de archivo y botón "Procesar factura".
6.2. Validar tipo y tamaño antes de enviar (D7).
6.3. Al elegir un archivo, generar `crypto.randomUUID()` y guardarlo con el archivo; "Reintentar" reusa la clave; otro archivo genera una nueva (D6).
6.4. Estados: `idle` → `processing` (botón deshabilitado, spinner) → `done` (número, proveedor, monto en USD y badge del dictamen, con enlace para abrir el Drawer) o `error` (mensaje y "Reintentar").
6.5. `201` y `200` iguales; `409` con hasta 3 reintentos automáticos cada 2 s con la misma clave.
6.6. Agregar la factura devuelta al inicio de la lista (o reemplazarla si ya está por `id`).

## 7. Reglas persistentes (F3.6)

7.1. `handleSaveRules` usa `saveRules` y solo actualiza `rules` con la respuesta.
7.2. `RuleControls.jsx` recibe `saving` y `errors`; muestra el error junto al campo según `loc` del `422` y un mensaje general para otros errores.
7.3. Confirmación breve de "Reglas guardadas" tras el `200`.
7.4. Deshabilitar guardar en modo demostración.

## 8. Recorrido, documentación y cierre

8.1. `npm run build` sin errores.
8.2. Levantar backend + PostgreSQL con seed en Docker y el frontend con `npm run dev`; recorrer el checklist manual de [validation.md](validation.md).
8.3. `frontend/README.md`: modo demostración, botón Actualizar, subida con `Idempotency-Key`, decisión humana con `decided_by` fijo; corregir el árbol de componentes.
8.4. `specs/roadmap.md`: marcar F3.1 a F3.6 con la fecha de verificación.
8.5. Completar [validation.md](validation.md) y abrir el PR.
