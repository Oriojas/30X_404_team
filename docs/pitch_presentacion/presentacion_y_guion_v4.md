# 🎬 Blinka PayAgent — Presentación y Guion Oficial V4 (Ajustes de Mentoría + Costos Operativos)

> **Documento de Trabajo para el Hackathon 30X (2da Edición)**
> **Equipo 404:** Oscar Riojas & Luis Felipe Marín Giraldo
> **Entregables:** Repositorio GitHub (`Oriojas/30X_404_team`) | Demo en Vivo (`30x404team-production.up.railway.app`)

---

## 📌 1. Qué cambia frente a la V3 (Retroalimentación de la Mentoría — 17 oct 2026)

Fuente: *Mentorías Hackathon (Oscar Riojas) — Notas de Gemini*. Mentora: Sandra Carrillo.

| # | Observación de la mentoría | Ajuste aplicado en la V4 |
| :--- | :--- | :--- |
| 1 | Las empresas destinatarias **ya conocen el problema**: abreviar el contexto inicial. | El gancho del lector biométrico baja de 42 s a **~20 s**. La slide del problema queda en una sola idea con 3 bullets cortos. |
| 2 | Ir **directo a la solución**, las tecnologías y la demo. | Solución y arquitectura se fusionan en una sola slide. La demo pasa a ocupar el bloque central del video. |
| 3 | Mostrar **tres ventanas simultáneas** con casos distintos: proveedor registrado, rechazado y escalado. | Nueva slide/escena de demo en **pantalla triple** (🟢 `AUTO_APPROVED` · 🔴 `REJECTED` · 🟠 `SCALED_TO_HUMAN`). |
| 4 | Incluir una **estimación de costos por llamada o por cada 1.000 llamadas**. | **Nueva slide final de costos operativos** (IA + infraestructura) con datos medidos en Gemini API y Railway CLI. No incluye el costo de desarrollo. |

> **Correcciones adicionales sobre la V3:** el modelo en producción es **Gemini 3.8 Flash** (`gemini-3.8-flash`, ver `backend/app/config.py`), no Gemini 1.5 Flash. La cuenta de cobro del biométrico escala por **`HITL-02` (proveedor nuevo)**. La factura de Oracle en EUR de la V3 no existe en `facturas_demo/` y se reemplaza por los documentos reales de demo.

---

## 📋 2. Estructura del Deck V4 (6 Diapositivas)

### 🖼️ Slide 1: Portada & Propuesta de Valor
- **Título:** Blinka PayAgent — *Agentes IA de decisión de pagos con gobernanza financiera*.
- **Subtítulo:** Cero pagos indebidos, normalización multidivisa y trazabilidad total… por menos de **1 centavo de dólar por factura**.
- **Visual:** Mockup de Telegram procesando la cuenta de cobro del biométrico (`SCALED_TO_HUMAN` ➔ `HUMAN_APPROVED`).
- **Footer:** Reto Blinka | Hackathon 30X | Equipo 404 | Desplegado en Railway.

---

### 🖼️ Slide 2: El Problema (versión corta)
- **Una frase:** *Lo recurrente está bajo control; lo imprevisto paraliza la tesorería.*
- **01. Imprevistos sin dueño:** la factura de un proveedor nuevo rebota entre correos y chats esperando una aprobación.
- **02. Fricción multidivisa:** COP, MXN, EUR, BRL o ARS pagados desde cuentas en USD.
- **03. Riesgo regulatorio:** duplicados y proveedores en listas SARLAFT / OFAC que se cuelan sin trazabilidad.

---

### 🖼️ Slide 3: La Solución y la Tecnología
- **Flujo:** Telegram / Portal web ➔ **Gemini 3.8 Flash** (OCR multimodal, 1 llamada por factura) ➔ **FX Engine** (USD) ➔ **Tubería determinista de 4 capas** (Python puro) ➔ **Audit Log** en PostgreSQL + Dashboard React.
- **Matriz de 4 estados:**
  1. 🟢 `AUTO_APPROVED` — proveedor verificado, con presupuesto y < $2,000 USD.
  2. 🔴 `REJECTED` — duplicado (< 30 días) o coincidencia en lista restrictiva.
  3. 🟠 `SCALED_TO_HUMAN` — supera el umbral, proveedor nuevo o saldo insuficiente.
  4. 🔵 `HUMAN_APPROVED` — el CFO aprueba en 1 clic desde el Dashboard.
- **Capas:** Compliance (SARLAFT/OFAC/ONU) · Integridad (duplicados, confianza OCR ≥ 85%) · Solvencia (presupuesto y saldo) · Gobierno HITL (umbral y proveedor nuevo).
- **Arquitectura hexagonal en FastAPI**, desplegada en Railway: Telegram hoy; WhatsApp o Email sin tocar el Core.
- **Nota clave:** *"La IA solo lee; las decisiones las toma código determinista y auditable. No se mueve dinero sin autorización."*

---

### 🖼️ Slide 4: Demo en Vivo — Tres Ventanas Simultáneas
Pantalla dividida en 3 columnas, cada una con su chat de Telegram (o el portal web) y, debajo, el Audit Log del Dashboard:

| Ventana | Caso | Documento | Monto | Resultado | Regla |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🟢 **1 — Proveedor registrado** | Factura recurrente de nube | `Factura_AWS_Cloud_Octubre.pdf` | 1,200,000 COP ➔ **$285.71 USD** | `AUTO_APPROVED` | — |
| 🔴 **2 — Rechazado** | Proveedor en lista OFAC | `backend/tests/fixtures/factura_global_trade.png` | — | `REJECTED` | `COMP-01` |
| 🟠 **3 — Escalado** | Técnico de emergencia del biométrico | `Cuenta_Cobro_Biometrico.pdf` | 450,000 COP ➔ **$107.14 USD** | `SCALED_TO_HUMAN` ➔ `HUMAN_APPROVED` | `HITL-02` |

> [!TIP]
> **Alternativa para la ventana 2:** reenviar `Factura_AWS_Cloud_Octubre.pdf` después de la ventana 1 ➔ `REJECTED` por `INTEG-01` (duplicado). Requiere grabar en orden; el caso OFAC funciona en paralelo.
> **Caso extra (opcional):** `Factura_Logistica_MX_Oct.pdf` (117,000 MXN ➔ $6,000 USD) ➔ `SCALED_TO_HUMAN` por `HITL-01` (supera el umbral).

---

### 🖼️ Slide 5: Impacto de Negocio
- **~90%** menos carga manual de revisión.
- **5+** divisas normalizadas automáticamente (COP, MXN, EUR, BRL, ARS ➔ USD).
- **0** pagos fuera de reglas.
- **1** sola llamada de IA por factura; el resto es código determinista.
- 🌐 `30x404team-production.up.railway.app` · 📦 `github.com/Oriojas/30X_404_team`

---

### 🖼️ Slide 6 (Final): Costos Operativos por Factura 💰

**Mensaje principal:** *Procesar una factura cuesta ~$0.005 USD de IA. 1.000 facturas al mes se operan con ~$10 USD, infraestructura incluida.*

#### A. Costo de IA por factura (Gemini 3.8 Flash, tier estándar)

| Concepto | PDF | Foto (PNG / Telegram) |
| :--- | :--- | :--- |
| Tokens de entrada (documento + prompt) | ~1,090 | ~1,600 |
| Tokens de salida (JSON 146 + razonamiento 903) | ~1,050 | ~1,050 |
| **Costo por factura** | **$0.0048** | **$0.0051** |
| **Costo por 1.000 facturas** | **$4.75** | **$5.14** |

#### B. Costo de infraestructura (Railway: backend + frontend + PostgreSQL)

| Concepto | Valor medido |
| :--- | :--- |
| Consumo real de las 3 apps en ~24 h (20 facturas procesadas) | **$0.039 USD** |
| Proyección mensual del consumo | **~$1.20 USD/mes** (96% es memoria siempre encendida) |
| Costo marginal de CPU + egress por factura | **< $0.00003 USD** |
| Piso de facturación (Plan Hobby, incluye $5 de consumo) | **$5 USD/mes** |

#### C. Costo total por volumen mensual

| Facturas / mes | IA | Infraestructura | **Total / mes** | **Costo por factura** |
| :--- | :--- | :--- | :--- | :--- |
| 100 | $0.50 | $5.00 | **$5.50** | $0.055 |
| 1,000 | $5.00 | $5.00 | **$10.00** | **$0.010 (~42 COP)** |
| 10,000 | $50.00 | $5.00 | **$55.00** | **$0.0055 (~23 COP)** |

- **Por cada 1.000 llamadas adicionales:** ~$5.03 USD (IA $5.00 + infraestructura marginal $0.03).
- **Escala:** a partir de unas 1.000 facturas/mes, la IA representa más del 50% del costo y la infraestructura casi no cambia.
- **Fuera del cálculo:** costo de desarrollo, Telegram (gratis) y dominio.

> **Footer de la slide:** *Precios oficiales de Gemini API válidos hasta el 31-dic-2026 ($0.75 / 1M de entrada · $3.75 / 1M de salida). Desde 2027 el precio se duplica: ~$10 por 1.000 facturas de IA. Infraestructura medida con `railway usage` el 17-oct-2026. TRM de referencia: 4,200 COP/USD.*

---

## 🎙️ 3. Guion Cronometrado para el Video Pitch (3 Minutos / 180 Segundos)

### ⏱️ Bloque 1: Gancho corto (0:00 – 0:20)
* **[0:00 - 0:20] (En cámara):**
  > *"Un sábado se daña el lector biométrico de la oficina. Llega un técnico de urgencia, lo arregla y deja su cuenta de cobro. Como es un proveedor nuevo, esa factura rebota semanas entre correos, se paga tarde y perdemos al único técnico que nos sacó del apuro.*
  > *Blinka PayAgent convierte esa foto en una decisión segura y auditable en segundos. Se los mostramos."*

---

### ⏱️ Bloque 2: Solución y Tecnología (0:20 – 0:50)
*(Slide 3 en pantalla)*
* **[0:20 - 0:50] (Voz en off):**
  > *"La factura llega por Telegram o por el portal web. Gemini 3.8 Flash hace el OCR en una sola llamada y devuelve un JSON estructurado. El FX Engine normaliza la moneda a dólares y una tubería de cuatro capas escrita en Python determinista decide: compliance contra SARLAFT y OFAC, integridad y duplicados, solvencia y, al final, el gobierno humano.*
  > *La IA solo lee; las decisiones las toma código auditable. Todo corre con arquitectura hexagonal en FastAPI, desplegada en Railway."*

---

### ⏱️ Bloque 3: Demo en Tres Ventanas (0:50 – 1:55)
*(Pantalla triple: tres chats de Telegram arriba y el Audit Log del Dashboard abajo)*

* **[0:50 - 1:10] Ventana 1 — Proveedor registrado 🟢:**
  > *"En la primera ventana enviamos la factura mensual de AWS por 1,200,000 pesos. El agente la convierte a $285.71 dólares, confirma que el proveedor está verificado, que hay presupuesto y que no supera el límite autónomo de $2,000 dólares: `AUTO_APPROVED`."*

* **[1:10 - 1:25] Ventana 2 — Rechazado 🔴:**
  > *"En la segunda llega una factura de Global Trade Partners. La capa de compliance la encuentra en la lista OFAC y la frena de inmediato: `REJECTED`, con la razón escrita en el log."*

* **[1:25 - 1:55] Ventana 3 — Escalado 🟠 ➔ Aprobado 🔵:**
  > *"En la tercera está nuestro técnico del biométrico: 450,000 pesos, $107 dólares. Es un proveedor nuevo, así que la regla `HITL-02` lo escala al CFO. En el Dashboard, el CFO lee la explicación, hace clic en 'Aprobar' y la factura pasa a `HUMAN_APPROVED`. El técnico recibe su confirmación en minutos, no en semanas."*

---

### ⏱️ Bloque 4: Impacto (1:55 – 2:15)
*(Slide 5 en pantalla)*
* **[1:55 - 2:15]:**
  > *"El resultado: cerca de un 90% menos de revisión manual, más de cinco divisas normalizadas y cero pagos fuera de reglas."*

---

### ⏱️ Bloque 5: Costos Operativos y Cierre (2:15 – 3:00)
*(Slide 6 — Costos en pantalla)*
* **[2:15 - 2:45] Costos:**
  > *"¿Cuánto cuesta operarlo? Medimos el consumo real. Cada factura usa unos dos mil tokens de Gemini: medio centavo de dólar. La infraestructura completa en Railway, con backend, frontend y base de datos, consume cerca de $1.20 al mes y cabe en el plan de $5.*
  > *Eso significa que mil facturas al mes cuestan unos diez dólares en total, un centavo por factura, y cada mil facturas adicionales suman unos cinco dólares."*

* **[2:45 - 3:00] Cierre:**
  > *"Blinka PayAgent ya está desplegado en Railway y el código es abierto en GitHub. Somos el Equipo 404. ¡Muchas gracias!"*

---

## 📊 4. Metodología del Cálculo de Costos (respaldo para preguntas del jurado)

### 4.1 IA — Gemini API
- **Modelo:** `gemini-3.8-flash`, configurado en `GEMINI_MODEL` (por defecto en `backend/app/config.py`).
- **Medición:** se ejecutó el mismo `EXTRACTION_PROMPT` y `EXTRACTION_SCHEMA` de `GeminiOCRAdapter` (`temperature=0`) sobre los 6 documentos de `facturas_demo/`, leyendo `usage_metadata` y `count_tokens`:

| Documento | Tokens de entrada | Salida (JSON) | Razonamiento | Total |
| :--- | :--- | :--- | :--- | :--- |
| `Factura_Logistica_MX_Oct.pdf` (llamada completa) | 1,079 | 146 | 903 | 2,128 |
| `Cuenta_Cobro_Biometrico.pdf` / `Factura_AWS_Cloud_Octubre.pdf` | 1,099 | ~146 | ~903 | ~2,148 |
| Versiones `.png` (equivalente a foto de Telegram) | 1,603 | ~146 | ~903 | ~2,652 |

> Las llamadas completas a los demás documentos devolvieron `503 UNAVAILABLE` (alta demanda del modelo en ese momento). Para ellos, la entrada se midió con `count_tokens` y la salida se tomó de la llamada completa (el JSON tiene un esquema fijo de 8 campos).

- **Precios oficiales** (`ai.google.dev/gemini-api/docs/pricing`, tier estándar pagado):
  - Hasta el 31-dic-2026: $0.75 / 1M de entrada · $3.75 / 1M de salida (incluye razonamiento).
  - Desde el 1-ene-2027: $1.50 / 1M de entrada · $7.50 / 1M de salida.
  - Batch / Flex: 50% del precio estándar.
- **Fórmula:** `costo = entrada × 0.75/1M + (salida + razonamiento) × 3.75/1M`
  - PDF: 1,090 × 0.75/1M + 1,049 × 3.75/1M = **$0.00475**
  - PNG: 1,603 × 0.75/1M + 1,049 × 3.75/1M = **$0.00514**

> [!NOTE]
> **Oportunidad de optimización (no implementada):** el ~83% del costo de IA viene de los tokens de razonamiento. Si se limita el razonamiento del modelo para la extracción, el costo bajaría a **~$1.40 – $1.75 por 1.000 facturas**. Hay que validar antes que la precisión del OCR no cambie.

### 4.2 Infraestructura — Railway CLI
Comandos usados (sin datos sensibles):
```bash
railway usage                                   # consumo del workspace en el periodo actual
railway usage projects --project <proyecto> --json   # desglose por servicio
railway metrics -p <project_id> -e production -a --since 2d   # CPU / memoria / volumen
```

Desglose del consumo medido en el periodo actual (~24 h, del 16 al 17 de octubre de 2026):

| Servicio | CPU | Memoria | Egress | Volumen | **Total** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `backend` (FastAPI) | $0.00047 | $0.01242 | $0.00014 | — | **$0.01303** |
| `Postgres` | $0.00018 | $0.01529 | — | $0.00034 | **$0.01581** |
| `30X_404_team` (frontend) | $0.00001 | $0.01020 | $0.00038 | — | **$0.01059** |
| **Total** | | | | | **$0.03943** |

- Recursos promedio: backend ~67 MB, Postgres ~55 MB (volumen 116 MB / 500 MB), frontend ~39 MB; CPU < 0.01 vCPU.
- Facturas procesadas en ese periodo (API, Web y Telegram): **20** ➔ costo marginal de CPU + egress del backend ≈ $0.0006 / 20 ≈ **$0.00003 por factura**.
- El costo está dominado por la memoria de 3 contenedores siempre encendidos, así que es un **costo fijo** que casi no crece con el volumen.
- **Plan Hobby:** $5 USD/mes que incluyen $5 de consumo. Con ~$1.20/mes proyectado, el piso real de infraestructura es de $5/mes.

---

## 🧪 5. Checklist para Grabar la Demo en Tres Ventanas

1. Abrir 3 ventanas de Telegram Web (o 2 de Telegram + 1 del portal) en mosaico, con el Dashboard de producción abierto abajo o en un segundo monitor.
2. Confirmar que la base tenga cargada la semilla de demostración (`DB_SEED_DEMO`, datos ficticios), para que el proveedor de AWS esté verificado y Global Trade Partners aparezca en la lista OFAC.
3. Si la ventana 2 usa el duplicado en vez de OFAC, enviar primero la ventana 1.
4. Antes de grabar, revisar que Gemini responda (en la medición del 17-oct hubo respuestas `503` por alta demanda). Si falla, la factura escala por `INTEG-03` y el demo pierde el caso esperado.
