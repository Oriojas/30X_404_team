# Requisitos — Validaciones pendientes, casos trampa y CI

> Rama: `feat/fase-5-validaciones-ci` · Fase 5 de [roadmap.md](../roadmap.md) (F5.1 a F5.7).
> Guía: [mission.md](../mission.md) y [tech-stack.md](../tech-stack.md).

## Contexto

Las Fases 2, 3 y 4 cerraron con su código mergeado y en producción, pero cinco verificaciones recomendadas quedaron sin marcar porque necesitaban el despliegue o un chat real:

| Pendiente | Dónde quedó sin marcar | Ítem |
| :--- | :--- | :--- |
| Aviso al chat tras aprobar en el Drawer | [frontend-api-real/validation.md](../2026-10-17-frontend-api-real/validation.md) | F5.1 |
| Update de Telegram repetido con un solo aviso | [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) | F5.2 |
| Archivo de Telegram subido después por la web (INTEG-01) | [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) | F5.3 |
| `Idempotency-Key` `201` → `200` | [ingesta-idempotente/validation.md](../2026-10-17-ingesta-idempotente/validation.md) | F5.4 |
| Build con `frontend/Dockerfile` | [frontend-api-real/validation.md](../2026-10-17-frontend-api-real/validation.md) | F5.4 |

Además, el reto enumera casos trampa que la demo debe mostrar. La Test Suite (TC-01 a TC-06) cubre duplicado, beneficiario nuevo, monto sobre el límite y saldo insuficiente, pero no "factura que no cuadra con lo acordado", aunque el código ya lo resuelve con INTEG-02 (tarifa pactada en `vendors.contract_amount_usd`). Por último, ningún PR corre las pruebas: hoy no existe `.github/workflows`.

## Alcance

**Entra (una sola rama, F5.1 a F5.7):**
- Las verificaciones en producción de F5.1 a F5.3, con evidencia registrada en el `validation.md` de origen.
- F5.4: marcar con referencia lo que ya se probó en la Fase 4 (segunda corrida de `humo_produccion.py` y el build del Dockerfile en Railway).
- F5.5: TC-07 en `casos_demo.py` (y por lo tanto en `humo_produccion.py` y `test_postgres_integration.py`), en la Test Suite de [reglas_pago_agente_v3.md](../../docs/reglas-negocio/reglas_pago_agente_v3.md) y en la tabla de casos de `backend/README.md`.
- F5.6: tiempo de arranque en frío del backend y captura del dashboard en producción, guardados para el pitch.
- F5.7: workflow de GitHub Actions con `pytest` y `npm run build` en cada PR.

**No entra:**
- TC-08 (presupuesto insuficiente): necesita editar el presupuesto (F7.6).
- PostgreSQL en el CI (F9.6): la integración sigue corriendo en local con `TEST_DATABASE_URL`.
- Protección de rama que exija el check: queda a criterio del equipo y no bloquea esta fase.
- Cambios en la tubería de reglas, en la API o en el frontend.

## Decisiones

| # | Decisión | Motivo |
| :--- | :--- | :--- |
| D1 | **TC-07 = factura de AWS por $1,500 USD** (`invoice_number` `AWS-2026-10-EXTRA`, mismo NIT `US-91-1646860`). AWS tiene historial y una tarifa pactada de $1,000; $1,500 queda bajo el umbral autónomo ($2,000) y deja $7,000 sobre el colchón. Solo dispara INTEG-02 → `SCALED_TO_HUMAN`, sin HITL-01, HITL-02, HITL-03 ni FIN. | Aísla el caso trampa: la única razón para escalar es que el monto no cuadra con lo acordado. Usa el seed tal como está, sin proveedores nuevos. |
| D2 | **`casos_demo.py` sigue siendo la fuente única.** Al agregar TC-07 a `CASOS`, `humo_produccion.py` y `test_postgres_integration.py` lo recorren sin cambios propios; solo se actualizan los textos que dicen "TC-01..TC-06". | Evita tres listas que se desincronicen. |
| D3 | **Claude ejecuta los pasos en producción** con el navegador integrado, `curl`, `humo_produccion.py` y la CLI de Railway (secretos leídos con `railway variables`, nunca escritos en el repo). La única acción humana es enviar la factura por Telegram desde el teléfono del equipo, porque un bot no puede escribirse a sí mismo como usuario. | Lo pidió el equipo: que Claude haga todo lo posible. |
| D4 | **F5.2 reutiliza el `update_id` real.** Se lee el último `external_id` del canal `telegram` en `ingested_messages` y se reenvía al webhook de producción un cuerpo con ese `update_id`, el mismo `chat_id` y un adjunto, con el header `X-Telegram-Bot-Api-Secret-Token`. La deduplicación de transporte ocurre antes de descargar el archivo, así que no hace falta el `file_id` original. | Prueba lo que importa (mismo update → `200 duplicate`, cero avisos nuevos) sin depender de capturar el cuerpo original, que no se registra en los logs. |
| D5 | **F5.3 sube por la web el mismo archivo que se envió por Telegram en F5.1** (un fixture de `backend/tests/fixtures`, enviado como documento para que Telegram no lo recomprima y el SHA-256 coincida). | Una foto comprimida por Telegram tiene otro hash; como documento conserva los bytes. |
| D6 | **Arranque en frío = tiempo desde `railway redeploy` del backend hasta el primer `GET /api/health` con `database: connected`**, más la latencia de esa primera respuesta. Se mide una vez y se anota con fecha. | Es el dato que importa en el pitch (cuánto tarda la demo en estar lista) y no requiere herramientas nuevas. |
| D7 | **CI mínimo:** un solo workflow `.github/workflows/ci.yml` con dos jobs en paralelo, en `pull_request` y en `push` a `master`. Backend: Python 3.12, `pip install -r backend/requirements.txt`, `pytest` desde `backend/` (la integración se omite sola sin `TEST_DATABASE_URL`). Frontend: Node 20, `npm ci` y `npm run build` en `frontend/`. Caché de pip y npm con las acciones oficiales `setup-python` y `setup-node`. | Las mismas versiones que los Dockerfiles; sin secretos ni servicios. |
| D8 | **Sin dependencias nuevas** en el backend ni en el frontend. El CI no se agrega a [tech-stack.md](../tech-stack.md) como tecnología nueva, pero sí se menciona en la fila de pruebas. | Pragmatismo de hackathon; la constitución exige registrar cambios de stack. |

## Contrato de TC-07

| Campo | Valor |
| :--- | :--- |
| Payload | `{"invoice_number": "AWS-2026-10-EXTRA", "vendor_name": "Amazon Web Services LATAM", "vendor_tax_id": "US-91-1646860", "original_amount": 1500}` |
| Decisión esperada | `SCALED_TO_HUMAN` |
| Regla en `audit_explanation` | `INTEG-02` |
| Fila de la Test Suite | Factura de proveedor frecuente por $1,500 USD cuando la tarifa pactada es $1,000 USD · **Trampa (No cuadra con lo acordado)** · `SCALED_TO_HUMAN` · `INTEG-02` |

## Restricciones

- El Core no cambia; la prueba de arquitectura sigue en verde.
- Ningún secreto (webhook, token del bot, URL de base de datos) entra al repo, al workflow ni a la evidencia.
- Cada `TC-0N` en producción crea facturas reales en el Audit Log público: la evidencia cita sus `id`.
- Documentación en español.
