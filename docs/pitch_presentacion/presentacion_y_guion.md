# Blinka PayAgent — Presentación Comercial y Guion para Video Pitch (3 Minutos)

**Hackathon 30X — Reto Blinka**  
**Equipo:** 30X 404 Team (`Oriojas/30X_404_team`)  
**Despliegue en Producción:** [30x404team-production.up.railway.app](https://30x404team-production.up.railway.app/)

> [!NOTE]
> **Alcance oficial del reto:** el agente **decide** (Pagar, Frenar o Escalar) y deja el registro explicable. **No ejecuta pagos reales ni mueve dinero** (ver `reglas_pago_agente_v3.md`, sección 1). En todo el pitch, "pagar" significa *aprobar y programar el pago*, nunca desembolsar fondos reales.

---

## 📌 PARTE 1: Estructura Diapositiva por Diapositiva (Slide Deck)

### Slide 1: Portada & Propuesta de Valor
* **Título Principal:** Blinka PayAgent — Agentes IA de Decisión de Pagos con Gobernanza Financiera.
* **Subtítulo:** Automatizando la decisión de pago de cuentas corporativas con cero pagos indebidos, conversión de divisas sin sobrecosto y trazabilidad total.
* **Mensaje Clave:** Transformamos la gestión manual de cuentas por pagar en un proceso autónomo, seguro y 100% auditable.
* **Elemento Visual:** Mockup interactivo dividido: a la izquierda el chat de Telegram enviando una factura; a la derecha la interfaz web de Blinka PayAgent con insignias de estado en tiempo real.

---

### Slide 2: El Problema Financiero (El Dolor en LatAm)
* **Título:** El Cuello de Botella de Cuentas por Pagar en Empresas Globales.
* **Puntos de Dolor:**
  1. **Ineficiencia Operativa:** Cientos de horas perdidas revisando facturas por correo, WhatsApp o PDF a mano.
  2. **Fricción Multidivisa:** Facturas de proveedores en COP, MXN, EUR, BRL o ARS pagadas desde cuentas de tesorería en USD, sufriendo altas comisiones de cambio (*FX Markups*).
  3. **Riesgo de Pagos Indebidos:** Alto riesgo de aprobar cobros duplicados (<30 días) o pagar a proveedores en listas restrictivas (SARLAFT/OFAC/ONU).
* **Métrica Impacto:** Las validaciones manuales repetitivas consumen la mayor parte del tiempo de los equipos de finanzas en PyMEs/Startups. *(Citar la fuente de la cifra exacta si se muestra un porcentaje en pantalla; si no hay fuente, usar el enunciado cualitativo.)*

---

### Slide 3: La Solución — Blinka PayAgent
* **Título:** Gobernanza Financiera Autónomamente Ejecutada.
* **Concepto:** Un agente inteligente conectado a Telegram que lee facturas multimodales, aplica las reglas de negocio de Blinka en tiempo real y emite la decisión idónea: **Pagar, Frenar o Escalar**.
* **Pilares Fundamentales:**
  * ⚡ **Autonomía:** Facturas de proveedores con historial verificado y por debajo de $2,000 USD (umbral configurable) se aprueban solas.
  * 🛡️ **Seguridad (Cero Pagos Indebidos):** Rechazo automático e inmediato de duplicados o coincidencias en listas restrictivas; cualquier duda se escala a un humano.
  * 📊 **Explicabilidad:** Justificación en lenguaje natural de cada decisión, sin abrir el código.

---

### Slide 4: Arquitectura Hexagonal y Pipeline Determinista de 4 Capas
* **Título:** Arquitectura Robusta, Escalable y Desacoplada.
* **Diagrama de Componentes:**
  * **Ingesta / Adaptadores:** Telegram Webhook y subida de archivos en el dashboard (desacoplados del Core; WhatsApp y correo como canales futuros). Los canales solo ingresan facturas: no aprueban.
  * **Core del Agente (FastAPI):**
    * **Gemini Flash (modelo configurable por `GEMINI_MODEL`):** únicamente OCR multimodal y extracción estructurada de campos (JSON).
    * **FX Engine:** normalización de divisas a USD con tasa de referencia y $0.00 FX Markup.
    * **Motor de Reglas Determinista:** código Python puro, **no** decidido por el LLM, lo que garantiza decisiones reproducibles y auditables.
    * **Audit Logger:** explicación en lenguaje natural por factura.
  * **Base de Datos (PostgreSQL en Railway):** Audit Log (`invoices`), reglas (`company_rules`), proveedores (`vendors`), listas restrictivas (`sanctions_list`) y tesorería (`treasury_accounts`).
  * **Dashboard (React + Tailwind):** auditoría, configuración de reglas y **aprobación humana** de las facturas escaladas.
* **Las 4 Capas de Validación (un rechazo crítico detiene la evaluación; las alertas de escalamiento se acumulan):**
  1. *Capa 1 — Compliance & SARLAFT:* listas restrictivas OFAC/ONU/GAFI (`REJECTED`), cuentas bancarias no autorizadas, PEP y consistencia del NIT (escalan a humano).
  2. *Capa 2 — Integridad & Datos:* duplicados en ventana de 30 días (`REJECTED`) y confianza OCR ≥ 85%.
  3. *Capa 3 — Solvencia:* saldo disponible en Blinka (USD) y presupuesto del período.
  4. *Capa 4 — Gobierno HITL:* umbral autónomo de $2,000 USD y proveedor nuevo escalan a revisión humana en el **dashboard**, donde queda registrado quién aprobó o rechazó (`HUMAN_APPROVED` / `HUMAN_REJECTED`).

---

### Slide 5: Demostración en Vivo & Audit Log
* **Título:** Transparencia y Control en Tiempo Real.
* **Contenido Visual:** Captura/Demo del Dashboard React desplegado en Railway: tabla de auditoría, panel de detalle por factura y controles de reglas (umbral, SARLAFT, ventana de duplicados).
* **Estados de Auditoría:**
  * 🟢 **`AUTO_APPROVED`:** Factura aprobada de forma autónoma.
  * 🔴 **`REJECTED`:** Frenado automático por duplicado o lista restrictiva.
  * 🟠 **`SCALED_TO_HUMAN`:** Escalada al gerente de finanzas por superar el umbral, proveedor nuevo o saldo insuficiente.
* **Detalle:** Explicación en lenguaje natural y código de regla disparada (`INTEG-01`, `HITL-01`, etc.) disponibles para consulta de auditoría o jurados.

---

### Slide 6: Impacto de Negocio, ROI y Siguientes Pasos
* **Título:** Resultados Medibles para Blinka y sus Clientes.
* **Métricas de Éxito:**
  * ⏱️ **Hasta ~90% menos carga manual** en el procesamiento de facturas *(estimación de diseño, ver `especificacion_solucion.md`; presentar como estimado, no como medición).*
  * 💵 **$0.00 en sobrecostos por cambio de divisa** gracias a la garantía FX de las cuentas Blinka.
  * 🔒 **Cero pagos indebidos por diseño:** ante cualquier duda, el agente frena o escala; nunca aprueba fuera de reglas.
  * 💲 **Costo operativo por factura mínimo:** una sola llamada a Gemini Flash por documento y reglas deterministas sin costo de inferencia. *(Medir el consumo real antes de mostrar una cifra.)*
* **Llamado a la Acción (CTA):** Solución desplegada en Railway, repositorio público con licencia MIT en GitHub y arquitectura lista para escalar a WhatsApp y correo corporativo.

---

## 🎬 PARTE 2: Guion Cronometrado para Video Pitch (3 Minutos Exactos)

> Estructura alineada con la guía oficial del reto: **Problema (0:00–0:30) → Demo funcional (0:30–2:00 aprox.) → Impacto y viabilidad (2:00–3:00)**.

| Tiempo | Seccion / Escena | Guion Hablado (Narrador / Presentador) | Accion Visual en Pantalla |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:15** | **El Gancho** | *"En América Latina, las empresas globales pierden cientos de horas procesando facturas manualmente por correo o WhatsApp, lidiando con monedas locales como pesos o euros, y arriesgándose constantemente a aprobar pagos duplicados."* | Primer plano del presentador o animación de caos financiero con hojas de cálculo y facturas en PDF. |
| **0:15 - 0:35** | **La Presentación** | *"Presentamos **Blinka PayAgent**: un agente inteligente de pagos corporativos que recibe facturas por Telegram, las lee con visión multimodal de Gemini, convierte divisas a USD sin sobrecosto y decide autónomamente qué pagar, qué frenar y qué escalar."* | Transición al logotipo de Blinka PayAgent y captura del dashboard en Railway (`30x404team-production.up.railway.app`). |
| **0:35 - 1:00** | **Demo Caso 1 (Aprobación Autónoma)** | *"Veamos la magia en acción. Enviamos por Telegram la foto de una factura en pesos colombianos de un proveedor ya conocido. El agente extrae los datos, convierte la cifra a USD, verifica listas restrictivas, valida el saldo y aprueba el pago en segundos."* | Grabación de pantalla: Envío de foto por Telegram $\rightarrow$ Respuesta del bot en Telegram $\rightarrow$ Aparece `AUTO_APPROVED` 🟢 en el Dashboard de React. |
| **1:00 - 1:25** | **Demo Caso 2 (Frenado por Duplicado)** | *"¿Qué pasa si intentan cobrarnos dos veces? Reenviamos la misma factura. El agente detecta de inmediato que ya existe un cobro idéntico en los últimos 30 días, frena la transacción y notifica el rechazo en Telegram, evitando un pago indebido."* | Reenvío de la factura en Telegram $\rightarrow$ El bot responde "Rechazado por factura duplicada" $\rightarrow$ Fila en rojo `REJECTED` 🔴 en el Audit Log. |
| **1:25 - 1:50** | **Demo Caso 3 (Escalamiento Human-in-the-Loop)** | *"Ahora enviamos una factura en euros equivalente a unos $3,480 USD. Como supera nuestro límite autónomo de $2,000 USD, el agente no paga: la deja en revisión, avisa por Telegram y el gerente la aprueba o rechaza desde el dashboard, dejando registrado quién decidió."* | Envío de factura de €3,200 EUR $\rightarrow$ El bot avisa que quedó en revisión $\rightarrow$ Fila en naranja `SCALED_TO_HUMAN` 🟠 $\rightarrow$ Aprobación en el dashboard (`HUMAN_APPROVED`). |
| **1:50 - 2:20** | **Explicabilidad & Dashboard** | *"Toda la operación se refleja en nuestro Dashboard en React desplegado en Railway. Al hacer clic en cualquier transacción, el equipo financiero lee la justificación exacta en lenguaje natural y la regla que se disparó, garantizando trazabilidad total. Y el umbral de autonomía es configurable desde el mismo panel."* | Navegación por la tabla de auditoría en el navegador, mostrando el panel de detalles, las justificaciones y el control de reglas. |
| **2:20 - 2:45** | **Arquitectura Hexagonal** | *"Diseñamos el sistema bajo arquitectura hexagonal en FastAPI. Gemini solo lee la factura; las decisiones las toma un motor de reglas determinista de cuatro capas, por eso cada resultado es reproducible y auditable. Telegram es solo un adaptador: podemos sumar correo o WhatsApp sin tocar la lógica de negocio."* | Diagrama de arquitectura de la solución mostrando la separación entre adaptadores, FastAPI, Gemini, motor de reglas y PostgreSQL. |
| **2:45 - 3:00** | **Cierre & ROI** | *"Blinka PayAgent reduce drásticamente el trabajo manual, elimina el sobrecosto por cambio de divisa y no aprueba nada fuera de las reglas. El repositorio es abierto y la app está funcionando en vivo. ¡Muchas gracias!"* | Pantalla final con URL de la app en Railway, enlace al repositorio de GitHub y QR de contacto. |

---

## 🛠️ PARTE 3: Guía de Verificación y Casos de Prueba para la Demo

Para asegurar que la grabación del video y la revisión de los jurados sea impecable:

> [!IMPORTANT]
> **Precondición de datos (seed):** la regla `HITL-02` escala a todo proveedor sin historial de pagos, y el agente busca al proveedor por NIT o por su razón social exacta. Las pruebas usan los proveedores del seed (`backend/app/adapters/outbound/db/seed.sql`), que ya tienen historial: la factura debe traer el mismo NIT o el mismo nombre que el seed. Con otro nombre y sin NIT (por ejemplo "AWS Cloud Services"), la Prueba 1 terminará en `SCALED_TO_HUMAN` por `HITL-02` y no en `AUTO_APPROVED`.

1. **Prueba 1 — Happy Path (COP/USD) · TC-01:**
   * *Factura:* Proveedor "Amazon Web Services LATAM" (NIT `US-91-1646860`, con historial), Monto: $1,200,000 COP (~$285.71 USD a tasa de referencia 4,200 COP/USD).
   * *Resultado esperado:* `AUTO_APPROVED` 🟢 (convertido a USD, sin coincidencias en listas restrictivas, saldo suficiente y dentro del límite de $2,000 USD).
2. **Prueba 2 — Intento de Duplicado · TC-02:**
   * *Factura:* Reenviar exactamente la misma factura de Amazon Web Services LATAM.
   * *Resultado esperado:* `REJECTED` 🔴 (`INTEG-01`: "Factura rechazada por detección de cobro duplicado" dentro de la ventana de 30 días).
3. **Prueba 3 — Exceso de Límite (EUR/USD) · TC-04:**
   * *Factura:* Proveedor "Nube Andina Consultores S.A.S." (NIT `901.223.450-1`, con historial y tarifa pactada de $5,000 USD), Monto: €3,200 EUR (~$3,478 USD a tasa de referencia 0.92 EUR/USD).
   * *Resultado esperado:* `SCALED_TO_HUMAN` 🟠 (`HITL-01`: "El monto excede el límite autónomo de $2,000 USD. Requiere aprobación manual"). Como Nube Andina tiene historial y la tarifa pactada cubre el monto, `HITL-01` es la única regla disparada.
4. **Prueba 4 (opcional, respaldo o corte extendido) — Lista Restrictiva · TC-06:**
   * *Factura:* Beneficiario simulado presente en la lista OFAC de prueba.
   * *Resultado esperado:* `REJECTED` 🔴 (`COMP-01`). Útil para demostrar la Capa 1 frente al jurado, ya que el guion cubre en vivo las capas 2 y 4.
5. **Prueba 5 (opcional) — Saldo Insuficiente · TC-05:**
   * *Factura:* $10,000 USD con saldo Blinka de $4,000 USD.
   * *Resultado esperado:* `SCALED_TO_HUMAN` 🟠 (`FIN-01`).
6. **Prueba 6 (opcional) — No cuadra con lo acordado · TC-07:**
   * *Factura:* "Amazon Web Services LATAM" (con historial) por $1,500 USD, cuando la tarifa pactada en contrato es de $1,000 USD.
   * *Resultado esperado:* `SCALED_TO_HUMAN` 🟠 (`INTEG-02`: "El valor cobrado supera la tarifa acordada en el contrato"). Está bajo el umbral autónomo y hay saldo: la única razón para escalar es que el monto no cuadra con lo acordado.

---

## ✅ PARTE 4: Checklist de Coherencia Antes de Grabar

El criterio de **Viabilidad Técnica (20%)** exige que el código respalde exactamente lo que se muestra en el video. Antes de grabar, verificar:

- [ ] El webhook de Telegram recibe fotos/PDF y responde. Ya está implementado (`adapters/inbound/telegram/webhook.py`, con `TELEGRAM_WEBHOOK_SECRET`); falta probarlo con el bot real registrado con `setWebhook`.
- [x] `adapters/outbound/ocr/gemini_ocr.py` llama realmente a Gemini (`google-genai`) y devuelve el JSON estructurado (Fase 1 del roadmap).
- [x] `core/domain/rules_pipeline.py` evalúa las 4 capas y devuelve la regla disparada (`INTEG-01`, `HITL-01`, etc.); TC-01 a TC-07 probados contra PostgreSQL.
- [x] `/api/invoices` y `/api/rules` leen y escriben en PostgreSQL.
- [ ] El Dashboard muestra datos reales de la API (hoy usa datos *mock* como respaldo): Fase 3 del roadmap.
- [ ] Los botones de aprobar/rechazar del dashboard llaman a `POST /api/invoices/{id}/decision` y actualizan el Audit Log (`HUMAN_APPROVED` / `HUMAN_REJECTED`). El backend ya está listo; falta el frontend (Fase 3).
- [ ] En Railway, el backend corre con `DB_AUTO_MIGRATE=true` (crea las tablas al arrancar) y `DB_SEED_DEMO=true` (proveedores con historial, listas restrictivas y saldo de $8,500 USD).
- [ ] Las tasas del FX Engine usadas en la demo coinciden con las cifras narradas (hoy son tasas de referencia fijas).
- [x] Textos de la landing sin respaldo en el código (SOC2, ISO 27001, AES-256, SLA, "dispersión bancaria", SPEI/ACH, latencias y KPIs inventados) ya fueron corregidos. Los datos del dashboard siguen siendo de demostración hasta conectar `/api/invoices`; no presentarlos como métricas reales en el video.

---

**Archivos de referencia en el proyecto:**
* [`docs/arquitectura/arquitectura_solucion_v5.md`](../arquitectura/arquitectura_solucion_v5.md)
* [`specs/roadmap.md`](../../specs/roadmap.md)
* [`plan_de_trabajo.md`](../../plan_de_trabajo.md)
* [`docs/reglas-negocio/reglas_pago_agente_v3.md`](../reglas-negocio/reglas_pago_agente_v3.md)
* [`docs/especificaciones/especificacion_solucion.md`](../especificaciones/especificacion_solucion.md)
