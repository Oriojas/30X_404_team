# 🎬 Blinka PayAgent — Presentación v2 y Guion para Video Pitch (3 Minutos)

> **Versión 2.0 (Actualizada con Presentación V2, Dashboard en Railway y Flujo Completo Human-in-the-Loop)**
> **Hackathon 30X — Reto Blinka Tech Corp**
> **Equipo 404 (30X_404_team)**

---

## 📊 Parte 1: Estructura Completa de Diapositivas (Pitch Deck V2)

### 📌 Slide 1: Portada & Propuesta de Valor
* **Título Principal:** Blinka PayAgent — Agentes IA de decisión de pagos con gobernanza financiera.
* **Subtítulo:** Cero pagos indebidos, conversión de divisas sin sobrecosto y trazabilidad total.
* **Tagline:** *Un proceso autónomo, seguro y 100% auditable.*
* **Elemento Visual:** Mockup interactivo de Telegram (Blinka PayBot) recibiendo la factura `Factura_AWS_Cloud.pdf` (1.4 MB) -> Extracción OCR con Gemini 1.5 Flash -> Conversión a **$285.71 USD** -> Estado **`AUTO_APPROVED`** 🟢.
* **Footer:** Blinka PayAgent | HACKATHON 30X · EQUIPO 404 · 01/06.

---

### 📌 Slide 2: El Problema (Cuello de Botella en Cuentas por Pagar)
* **Encabezado:** El cuello de botella de cuentas por pagar en empresas globales de LatAm.
* **01. Ineficiencia operativa ⏱️:** Cientos de horas perdidas revisando facturas por correo, WhatsApp o PDF a mano.
* **02. Fricción multidivisa 💱:** Facturas recibidas en monedas locales (**COP, MXN, EUR, BRL, ARS**) pagadas desde tesorerías en **USD**, generando altas comisiones y discrepancias cambiarias.
* **03. Riesgo de pagos indebidos 🚨:** Cobros duplicados en menos de 30 días o proveedores en listas restrictivas de cumplimiento que pasan inadvertidos.
* **Mensaje Clave:** *Las validaciones manuales repetitivas consumen la mayor parte del tiempo de los equipos de finanzas y exponen a la empresa a pérdidas de capital.*

---

### 📌 Slide 3: La Solución (Gobernanza Financiera Autónomamente Ejecutada)
* **Encabezado:** Gobernanza financiera autónomamente ejecutada.
* **Concepto:** Un agente conectado a Telegram lee facturas multimodales, aplica las reglas de negocio deterministas de Blinka y emite la decisión idónea.
* **Matriz de Decisiones:**
  * 🟢 **`AUTO_APPROVED` (Pagar):** Proveedor verificado en lista permitida, dentro del límite autónomo (< $2,000 USD) y con saldo suficiente.
  * 🔴 **`REJECTED` (Frenar):** Cobro duplicado (< 30 días) o coincidencia en lista restrictiva de cumplimiento.
  * 🟠 **`SCALED_TO_HUMAN` (Escalar):** Supera el umbral, proveedor nuevo sin verificar o saldo insuficiente. Decide una persona en el dashboard.
  * 🔵 **`HUMAN_APPROVED` (Aprobado en Dashboard):** Decisión revisada y autorizada por el CFO/gerente con justificación registrada en el Audit Log.
* **Pilares de Confianza:**
  * **Autonomía:** Facturas de la lista permitida y bajo $2,000 USD se aprueban solas.
  * **Seguridad:** Rechazo inmediato de duplicados y listas restrictivas; ante la duda, escala.
  * **Explicabilidad:** Cada decisión cuenta con justificación en lenguaje natural y regla específica disparada.
  * *Aclaración técnica:* El agente decide y registra; no ejecuta pagos reales ni mueve dinero.

---

### 📌 Slide 4: Arquitectura Hexagonal y Pipeline de 4 Capas
* **Encabezado:** Arquitectura Hexagonal, desacoplada y determinista.
* **Componentes de Entrada:** Telegram (Bot MVP) / WhatsApp & Correo (Canales futuros desacoplados).
* **Core del Agente (FastAPI en Railway):**
  1. **Gemini 1.5 Flash:** OCR multimodal + extracción estructurada en JSON.
  2. **FX Engine:** Normalización automática de 5+ divisas a USD mediante tasas de mercado ($0.00 markup).
  3. **Reglas Blinka:** 4 capas deterministas evaluadas en código Python (sin costo de LLM ni riesgo de alucinación).
  4. **Audit Logger:** Generación de explicación en lenguaje natural.
* **Persistencia & UI:** Base de Datos PostgreSQL + Dashboard en React.js.
* **Pipeline Determinista de 4 Capas (Se detiene ante la primera falla crítica):**
  * **Capa 1 — Compliance & SARLAFT:** Verificación en listas restrictivas, validación de cuentas bancarias, PEP y NIT/RUT.
  * **Capa 2 — Integridad:** Detección de duplicados en ventana de 30 días y confianza OCR ≥ 85%.
  * **Capa 3 — Solvencia:** Verificación de saldo en cuenta Blinka y presupuesto asignado del período.
  * **Capa 4 — Gobierno HITL:** Control de umbral autónomo ($2,000 USD) y bandera de proveedor nuevo.

---

### 📌 Slide 5: Demo & Audit Log en Vivo
* **Encabezado:** Transparencia y control en tiempo real.
* **Tabla de Auditoría (Casos de Prueba Reales):**
  | Proveedor | Monto Original | Equivalente USD | Estado | Regla Disparada | Explicación en Lenguaje Natural |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | **AWS Cloud Services** | 1,200,000 COP | **$285.71** | 🟢 `AUTO_APPROVED` | — | Proveedor verificado, saldo suficiente y dentro del límite autónomo. |
  | **AWS Cloud Services** | 1,200,000 COP | **$285.71** | 🔴 `REJECTED` | `INTEG-01` | Cobro duplicado detectado dentro de la ventana de 30 días. |
  | **Oracle Enterprise** | 3,200 EUR | **$3,478.26** | 🟠 `SCALED_TO_HUMAN` | `HITL-01` | Excede el límite autónomo de $2,000 USD. Requiere aprobación humana. |
  | **Logística Express MX** | 117,000 MXN | **$6,000.00** | 🔵 `HUMAN_APPROVED` | `HITL-01` | Escalada por el umbral; aprobada por el CFO en el dashboard, con nota en el Audit Log. |
* **Características de la UI:** Umbral configurable, detalle desplegable por factura, regla disparada visual y aprobación humana interactiva en el dashboard.
* **Enlace a la Demo:** En producción en Railway

---

### 📌 Slide 6: Impacto y Viabilidad de Negocio
* **Encabezado:** Resultados medibles para Blinka y sus clientes.
* **Métricas Clave:**
  * **~90%** menos carga manual en equipos de cuentas por pagar.
  * **5+ divisas** normalizadas automáticamente (COP, MXN, EUR, BRL, ARS a USD).
  * **0 pagos fuera de reglas** (Garantizado por diseño: ante la menor duda, el sistema frena o escala).
  * **1 sola llamada a Gemini por factura** (El OCR y la estructuración JSON se ejecutan en 1 inferencia; las reglas corren en código puro sin latencia ni costo recurrente).
* **Infraestructura y Despliegue:**
  * 🌐 **Demo en Producción:** Desplegada en Railway.
  * 💻 **Código Abierto en GitHub:** Disponible en el repositorio del equipo.
  * Listo para escalar a WhatsApp y correo corporativo sin alterar la lógica del negocio.

---

## 🎬 Parte 2: Guion Cronometrado para el Video Pitch (3 Minutos / 180 Segundos)

### ⏱️ Bloque 1: El Gancho y el Problema Financiero (0:00 - 0:35)
* **Pantalla:** Diapositiva 1 y 2 + Cámara del presentador.
* **Locución (Voz entusiasta y clara):**
  > *"Hola a todos. En América Latina, las empresas globales pierden cientos de horas revisando facturas a mano en correos, archivos PDF o chats de WhatsApp. Además, sufren comisiones cambiarias desproporcionadas al pagar proveedores en pesos colombianos, mexicanos o euros desde sus tesorerías en dólares, corriendo el riesgo constante de aprobar cobros duplicados o proveedores no autorizados.
  >
  > Para resolver esto creamos **Blinka PayAgent**: un agente financiero autónomo basado en arquitectura hexagonal que procesa facturas multimodales desde Telegram, normaliza divisas a USD sin sobrecostos y decide con cero margen de error qué pagar, qué frenar y qué escalar a una persona, dejando un registro 100% auditable."*

---

### ⏱️ Bloque 2: Demostración en Vivo en Producción (0:35 - 1:45)
* **Pantalla:** Pantalla dividida (Telegram a la izquierda, Dashboard en Railway a la derecha).

* **0:35 - 1:00 | Caso 1 — Aprobación Autónoma (`AUTO_APPROVED` 🟢):**
  > *"Veamos el sistema operando en tiempo real. Un empleado envía a nuestro Bot de Telegram la foto de una factura de **AWS Cloud** por 1,200,000 pesos colombianos. El adaptador descarga el documento y **Gemini 1.5 Flash** extrae los datos estructurados en una sola llamada. Nuestro **FX Engine** convierte el monto a $285.71 USD, la Capa 1 de Compliance verifica que es un proveedor autorizado, la Capa 3 confirma que hay saldo suficiente y, al estar por debajo del límite de $2,000 USD, se aprueba automáticamente en segundos."*

* **1:00 - 1:20 | Caso 2 — Detección de Duplicado (`REJECTED` 🔴):**
  > *"¿Qué sucede si nos intentan cobrar dos veces la misma factura? Reenviamos el mismo archivo por Telegram. La Capa 2 de Integridad detecta en tiempo real que existe un registro idéntico procesado en los últimos 30 días (`INTEG-01`), frenando la transacción inmediatamente y emitiendo un rechazo con alerta de seguridad."*

* **1:20 - 1:35 | Caso 3 — Escalamiento por Umbral (`SCALED_TO_HUMAN` 🟠):**
  > *"Ahora enviamos una factura de **Oracle Enterprise** en Euros por 3,200 EUR ($3,478.26 USD). Al superar nuestro límite autónomo de $2,000 USD, la Capa 4 de Gobierno frena el pago y marca la transacción como escalada a revisión humana (`HITL-01`)."*

* **1:35 - 1:45 | Caso 4 — Aprobación Humana en Dashboard (`HUMAN_APPROVED` 🔵):**
  > *"Pasamos al Dashboard de Blinka en Railway. El CFO revisa la factura de **Logística Express MX** por $6,000 USD escalada previamente, lee la justificación en lenguaje natural y hace clic en **Aprobar**. El estado se actualiza en vivo a `HUMAN_APPROVED`, completando el ciclo Human-in-the-Loop."*

---

### ⏱️ Bloque 3: Arquitectura Hexagonal y Seguridad (1:45 - 2:20)
* **Pantalla:** Diapositiva 4 (Esquema de Arquitectura).
* **Locución:**
  > *"La clave de nuestra confiabilidad es nuestra **Arquitectura Hexagonal**. Separamos los adaptadores de canal (como Telegram) del Core en FastAPI. Si Blinka decide añadir ingesta por correo o WhatsApp en el futuro, no se modifica una sola línea del motor de reglas.
  >
  > Además, nuestro pipeline de 4 capas es **determinista en código Python**: no usamos modelos de lenguaje para aplicar las reglas contables, lo que garantiza **cero alucinaciones** y un tiempo de ejecución de milisegundos sin costos recurrentes de inferencia."*

---

### ⏱️ Bloque 4: Impacto de Negocio, ROI y Cierre (2:20 - 3:00)
* **Pantalla:** Diapositiva 6 y Vista del Repositorio de GitHub.
* **Locución:**
  > *"Blinka PayAgent reduce hasta un **90% la carga manual** en cuentas por pagar, normaliza **más de 5 divisas** a tasa oficial sin markups y garantiza **cero pagos indebidos**, ya que ante la menor ambigüedad el sistema frena o escala.
  >
  > El sistema está totalmente desplegado en producción en Railway y el repositorio de código está disponible en GitHub. ¡Muchas gracias!"*

---

## 🛠️ Parte 3: Datos de Prueba para la Ejecución de la Demo

Para realizar la grabación del video o las pruebas en vivo de la aplicación, utilicen los siguientes registros estándar:

| # | Caso de Prueba | Canal | Documento / Datos | Moneda Original | USD Convertido | Estado Esperado | Regla |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Factura Recurrente | Telegram | `Factura_AWS_Cloud.pdf` | $1,200,000 COP | $285.71 USD | 🟢 `AUTO_APPROVED` | — |
| **2** | Cobro Duplicado | Telegram | `Factura_AWS_Cloud.pdf` (Reenvío) | $1,200,000 COP | $285.71 USD | 🔴 `REJECTED` | `INTEG-01` |
| **3** | Exceso de Umbral | Telegram | `Factura_Oracle_EUR.pdf` | €3,200 EUR | $3,478.26 USD | 🟠 `SCALED_TO_HUMAN` | `HITL-01` |
| **4** | Flujo HITL Aprobado | React UI | `Factura_Logistica_MX.pdf` | $117,000 MXN | $6,000.00 USD | 🔵 `HUMAN_APPROVED` | `HITL-01` |

---

## 🚀 Instrucciones de Publicación en el Repositorio

Para sincronizar este documento dentro de la estructura monorepo de GitHub:

1. Guardar este archivo como `docs/presentacion_y_guion_v2.md` o en la raíz del repositorio.
2. Sincronizar el repositorio local con `git commit` y `git push`.
