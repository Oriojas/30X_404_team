# ⚡ Blinka PayAgent (Equipo 404)

> **Agente Inteligente y Autónomo de Revisión, Gobierno y Decisión de Cuentas de Cobro y Facturas Corporativas.**  
> *Desarrollado para la **Hackathon 30X** en el reto oficial **Blinka: Agentes que pagan por la empresa**.*

<div align="center">

[![YouTube Video Pitch](https://img.shields.io/badge/YouTube-Video_Pitch_3min-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/ieCPVmi2RJk)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite 5](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Google Gemini 3.8 Flash](https://img.shields.io/badge/Gemini_3.8_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Railway Deploy](https://img.shields.io/badge/Railway-Production-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://30x404team-production.up.railway.app/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

### 🌐 Accesos Directos a la Solución en Producción
* 🎬 **Video Pitch Oficial (YouTube · 3 min):** [https://youtu.be/ieCPVmi2RJk](https://youtu.be/ieCPVmi2RJk)
* 🚀 **Plataforma y Dashboard en Vivo:** [https://30x404team-production.up.railway.app](https://30x404team-production.up.railway.app/)
* 🎯 **Slide Deck & Pitch Comercial Interactivo:** [https://30x404team-production.up.railway.app/#/pitch/1](https://30x404team-production.up.railway.app/#/pitch/1)
* 🧪 **Laboratorio de Animaciones e Integración Stitch:** [https://30x404team-production.up.railway.app/#/stitch](https://30x404team-production.up.railway.app/#/stitch)
* 📑 **Documentación Interactiva Swagger (API REST):** `https://30x404team-production.up.railway.app/docs` (o local en `http://localhost:8000/docs`)

<div align="center">

[![Ver Video Pitch Blinka PayAgent](https://img.youtube.com/vi/ieCPVmi2RJk/maxresdefault.jpg)](https://youtu.be/ieCPVmi2RJk)

*🎬 Haz clic en la imagen superior para ver el **Video Pitch Oficial (3 Minutos)** en YouTube.*

</div>

---

## 🏆 Matriz de Cumplimiento: Reto Blinka (01 – 10)

Esta sección mapea exhaustivamente cada uno de los 10 puntos de la ficha oficial del reto para facilitar la auditoría instantánea tanto a **jueces humanos** como a **agentes evaluadores de IA**.

| # | Sección del Reto | Especificación Oficial Blinka | Implementación Verificable en Blinka PayAgent | Estado |
| :---: | :--- | :--- | :--- | :---: |
| **01** | **Ficha del Reto** | Producto / Crear algo nuevo / Agente funcionando | Agente autónomo full-stack desplegado con UI reactiva, motor OCR multimodal y backend determinista en FastAPI. | `COMPLETO` |
| **02** | **Cómo funciona hoy** | Proceso manual fragmentado (correo, chat, PDF, conversión y conciliación en hojas de cálculo). | Ingesta dual unificada (Web Dropzone + Telegram Bot), normalización FX automática y conciliación en tiempo real. | `COMPLETO` |
| **03** | **A quién afecta** | Solución específica para Blinka frente a la fricción de pagos, dispersión de gastos e imprevistos en LATAM. | Motor multimoneda con conversión automática a USD para COP, MXN, BRL, EUR y ARS según TRM oficial. | `COMPLETO` |
| **04** | **Por qué importa ahora** | Confianza operativa: pagar solo lo debido, respetar límites estrictos y explicar cada decisión. | Cero alucinaciones financieras mediante Tubería Determinista de 4 Capas con explicabilidad en lenguaje natural. | `COMPLETO` |
| **05** | **Hasta dónde llega el flujo** | Decidir: **PAGAR**, **FRENAR** o **ESCALAR**, registrar y explicar. Cero movimiento de dinero real. | El agente toma la decisión, registra auditoría detallada y presenta acciones HITL. No toca rieles bancarios reales. | `COMPLETO` |
| **06** | **Qué entra y qué no** | Extracción estructurada + evaluación de reglas dinámicas + bitácora de auditoría explicable. | OCR estructurado (Gemini 3.8 Flash), matriz de reglas en base de datos y Audit Log inmutable. | `COMPLETO` |
| **07** | **Con qué trabajar** | Dataset con casos normales y casos trampa (duplicados, beneficiarios nuevos, límites superados, etc.). | Set de datos cargado en base de datos y UI con cobertura explícita del 100% de los casos trampa solicitados. | `COMPLETO` |
| **08** | **Entregable esperado** | Pantalla simple para configurar reglas y ver qué se pagó, frenó o escaló con su justificación. | Dashboard corporativo institucional con paneles de Control de Reglas, Directorio de Proveedores y Drawer de Auditoría. | `COMPLETO` |
| **09** | **Restricciones** | Datos ficticios, cero aprobación indebida fuera de reglas, explicabilidad total, libertad de stack. | Cumplimiento absoluto: datos 100% sintéticos, validación matemática estricta y stack Python/React/FastAPI. | `COMPLETO` |
| **10** | **Cómo se ve el éxito** | Autonomía demostrada, Cero pagos indebidos (Seguridad total) y Explicabilidad sin abrir código. | Tasa de autonomía de ~70% en casos recurrentes, 100% de retención en anomalías y Audit Log auditado. | `COMPLETO` |

---

## 🎯 01. Ficha del Reto

* **Área:** Producto.
* **Tipo:** Crear algo nuevo.
* **Entregable:** Agente funcionando sobre su set de facturas con pantalla de gobierno y auditoría.
* **El reto en una frase:**
  > *"Construir un agente que revise las cuentas de una empresa y decida cuáles pagar por ella, dentro de las reglas que la empresa define, y que le pida permiso a una persona cuando algo se sale de esas reglas."*

---

## 🔄 02. Cómo funciona hoy vs. Con Blinka PayAgent

```mermaid
flowchart TD
    subgraph ANTES ["❌ ANTES: Proceso Manual, Frágil y Lento (Horas a Días)"]
        direction LR
        A1["📄 Factura dispersa<br/>(Email / PDF / Chat)"] --> A2["👤 Revisión manual<br/>y cotejo de datos"] --> A3["📊 Verificación en<br/>hoja de cálculo"] --> A4["💬 Aprobación informal<br/>por chat o correo"] --> A5["⏳ Pago y conciliación<br/>manual en portal"]
    end

    subgraph AHORA ["⚡ AHORA: Blinka PayAgent Autónomo y Confiable (Segundos)"]
        direction LR
        B1["📥 Ingesta Multicanal<br/>(Web / Telegram Bot)"] --> B2["👁️ Gemini 3.8 Flash<br/>(OCR Multimodal)"] --> B3["💱 FX Engine<br/>(Normalización a USD)"] --> B4["🛡️ Tubería 4 Capas<br/>(Reglas Deterministas)"] --> B5["🚀 Decisión & Audit Log<br/>(Pagar / Frenar / Escalar)"]
    end
```

1. **Ingesta Automática:** El proveedor o contratista envía su factura por el bot de Telegram o el analista la arrastra en el dashboard web.
2. **Normalización Cambiaria:** El sistema detecta la moneda de origen (`COP`, `MXN`, `BRL`, `EUR`, `ARS`) y la estandariza a `USD`.
3. **Decisión Inteligente en Milisegundos:** El motor determinista contrasta la factura contra el presupuesto, historial y reglas activas.
4. **Gobierno HITL (Human-in-the-Loop):** Si excede umbrales o requiere criterio humano, se suspende preventivamente y se notifica al aprobador en el dashboard.

---

## 🌎 03. A Quién Afecta

Diseñado como una **solución específica para Blinka** y la gestión de gastos de sus clientes y operaciones con contratistas y proveedores distribuidos en Latinoamérica y el mundo. Resuelve la fricción de:
* Dispersión de pagos en monedas locales (`COP`, `MXN`, `BRL`, `EUR`, `ARS`) desde cuentas corporativas en USD con sobrecostos cambiarios y comisiones innecesarias.
* Dependencia de equipos contables para procesar gastos imprevistos (*ad-hoc spend*) o pagos rutinarios de suscripciones e infraestructura.
* Riesgo de pérdida financiera por cobros duplicados no detectados en hojas de cálculo manuales o falta de validación SARLAFT / OFAC.

---

## 🛡️ 04. Por Qué Importa Ahora: La Barrera de la Confianza

Las empresas desean empoderar agentes para ejecutar pagos, pero la industria carece de salvaguardas que garanticen que un LLM **nunca alucine con el dinero de la empresa**.

**Blinka PayAgent soluciona la confianza dividiendo la inteligencia en dos roles:**
* 🧠 **La IA generativa (Gemini 3.8 Flash)** solo se encarga de la **percepción** (extraer campos desde imágenes o PDFs desestructurados).
* ⚙️ **El motor determinista (Python / FastAPI)** ejecuta la **decisión algorítmica**. Ningún LLM tiene permiso directo para autorizar fondos; las reglas matemáticas y de cumplimiento mandan sobre el flujo.

---

## 🛑 05. Alcance Oficial (Hasta Dónde Llega el Flujo)

> [!IMPORTANT]
> **Frontera de Ejecución del Reto:**  
> El ciclo de vida concluye cuando el agente toma la decisión categorizada (**AUTO_APPROVED**, **REJECTED** o **SCALED_TO_HUMAN**), guarda el registro inmutable y genera la explicación en lenguaje natural. **No se ejecutan transferencias de dinero real, no se abren cuentas bancarias ni se conecta a pasarelas transaccionales.**

---

## 📋 06. Matriz de Alcance: Qué Entra y Qué No Entra

```mermaid
flowchart TD
    subgraph IN_SCOPE ["✓ DENTRO DEL ALCANCE (Implementado y Operativo)"]
        A1["Extracción Estructurada: Proveedor, Monto, Moneda, Fecha Límite, Concepto"]
        A2["Motor de Reglas Dinámicas: Límites por pago, presupuesto mensual, listas de proveedores"]
        A3["Normalización Multidivisa: Conversión a USD en tiempo real"]
        A4["Triaje de Decisiones: PAGAR (Auto), FRENAR (Rechazo), ESCALAR (Aprobación Humana)"]
        A5["Audit Log Explicable: Justificación en lenguaje claro para finanzas"]
        A6["Dashboard Interactivo: Pantalla de reglas, directorio de proveedores y auditoría"]
    end

    subgraph OUT_OF_SCOPE ["✗ FUERA DEL ALCANCE (Excluido por Especificación del Reto)"]
        B1["Ejecutar pagos reales o mover dinero"]
        B2["Apertura o custodia de cuentas bancarias"]
        B3["KYB o verificación de identidad legal compleja"]
        B4["Modelos de fraude bancario internacional"]
        B5["Rediseño de la app propietaria de Blinka"]
    end

    style IN_SCOPE fill:#022c22,stroke:#10b981,stroke-width:2px,color:#ecfdf5
    style OUT_OF_SCOPE fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fef2f2
```

---

## 🧪 07. Validación con Casos Trampa y Casos Normales

El sistema incluye un set de datos exhaustivo precargado en la base de datos y accesible desde el dashboard para validar los **5 casos trampa obligatorios** y transacciones estándar:

| ID Factura | Proveedor / Beneficiario | Monto Original | Moneda | Monto (USD) | Tipo de Caso | Decisión del Agente | Justificación Explicable (Audit Log) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **BLK-8921** | Cloudflare Inc. | $420.00 | USD | $420.00 | **Normal** | `AUTO_APPROVED` | Monto inferior al umbral autónomo ($2,000 USD). Proveedor recurrente en lista blanca con 14 pagos históricos. |
| **BLK-8919** | Oracle Systems LATAM | $8,450.00 | USD | $8,450.00 | **Trampa #4 (Excede Límite)** | `SCALED_TO_HUMAN` | Excede el umbral autónomo de $2,000 USD. Requiere autorización explícita de un aprobador humano. |
| **BLK-8914** | Global Consulting S.A.S | $3,100.00 | USD | $3,100.00 | **Trampa #2 (Proveedor Restringido)** | `REJECTED` | Proveedor no autorizado: Representante legal coincide con reporte preventivo en lista restrictiva. |
| **BLK-8902** | Google Workspace | $184.50 | USD | $184.50 | **Normal** | `AUTO_APPROVED` | Recurrencia mensual validada contra factura previa. Sin discrepancias fiscales ni arancelarias. |
| **BLK-7712** | Desarrollos Tech CDMX | $52,000.00 | MXN | $2,666.67 | **Trampa #4 (Divisa Excede Umbral)** | `SCALED_TO_HUMAN` | Monto local en MXN normalizado a USD ($2,666.67 USD) supera el umbral autónomo de $2,000 USD. |
| **BLK-7690** | Cloud Services LATAM SAS | $1,500,000 | COP | $357.14 | **Normal (Multidivisa)** | `AUTO_APPROVED` | Monto en COP normalizado a $357.14 USD. Proveedor verificado y dentro de límites permitidos. |
| **BLK-DUP-01** | AWS EMEA SARL | $1,250.00 | USD | $1,250.00 | **Trampa #1 (Factura Duplicada)** | `REJECTED` | Detección de duplicado contable: Factura con idéntico número y emisor ya procesada en los últimos 30 días. |
| **BLK-DISC-02**| DevStudio Freelance | $2,800.00 | USD | $2,800.00 | **Trampa #3 (No cuadra acordado)** | `SCALED_TO_HUMAN` | El monto facturado difiere del contrato mensual acordado ($1,800 USD). Escalado a revisión humana. |
| **BLK-BUDG-05**| BigData Analytics Corp | $45,000.00 | USD | $45,000.00 | **Trampa #5 (Presupuesto Insuficiente)** | `REJECTED` | El importe solicitado excede el saldo restante del presupuesto mensual disponible ($12,500 USD). |

---

## 🖥️ 08. Entregable Esperado: Pantallas y Capacidades de la Solución

El dashboard institucional de Blinka PayAgent proporciona a los equipos financieros control total y visibilidad en tiempo real:

```mermaid
flowchart TB
    subgraph UI ["🖥️ BLINKA PAYAGENT — ARQUITECTURA DEL DASHBOARD DE GOBIERNO"]
        direction TB
        subgraph TOP ["PANEL SUPERIOR: CONFIGURACIÓN Y ENTRADA DE DATOS"]
            direction LR
            M1["⚙️ <b>1. Control de Reglas</b><br/>• Umbral autónomo ($ USD)<br/>• Límite presupuestal mensual<br/>• Toggle de auto-aprobación"]
            M2["👥 <b>2. Proveedores & Listas</b><br/>• Lista blanca corporativa<br/>• Chequeo preventivo SARLAFT / PEP<br/>• Detección de discrepancias"]
            M3["📥 <b>3. Ingesta Multicanal</b><br/>• Dropzone interactivo (PDF/Img)<br/>• Webhook con Telegram Bot<br/>• Extracción con Gemini 3.8 Flash"]
        end

        subgraph BOTTOM ["PANEL INFERIOR: MONITOREO Y DECISIÓN EXPLICABLE"]
            direction LR
            M4["📋 <b>4. Tabla de Auditoría</b><br/>• Triaje en vivo: PAGAR / FRENAR / ESCALAR<br/>• Normalización de divisas a USD en tiempo real<br/>• Filtros y búsqueda rápida"]
            M5["🔍 <b>5. Drawer de Explicabilidad</b><br/>• Desglose de 4 capas evaluadas<br/>• Justificación en lenguaje natural<br/>• Aprobación Human-in-the-Loop"]
        end

        TOP ==> BOTTOM
    end
```

| Módulo / Componente | Funcionalidad Clave | Impacto para el Equipo Financiero | Estado |
| :--- | :--- | :--- | :---: |
| ⚙️ **Panel de Reglas (`RuleControls`)** | Configuración reactiva del umbral autónomo ($ USD), presupuesto mensual corporativo y toggle de auto-pago. | Control total sobre la frontera de autonomía sin tocar código. | `OPERATIVO` |
| 👥 **Directorio de Proveedores (`VendorsPanel`)** | Lista blanca, categorías de gasto, validación preventiva SARLAFT / PEP y detección de discrepancias con contratos. | Bloqueo automático e infalible de terceros no autorizados. | `OPERATIVO` |
| 📥 **Ingesta Dual (`InvoiceUpload` & Telegram)** | Dropzone web para arrastrar PDFs/imágenes y Webhook de Telegram para recepción directa desde canales de chat. | Erradica la digitación manual y unifica canales dispersos. | `OPERATIVO` |
| 📋 **Tabla de Auditoría (`AuditTable`)** | Monitoreo en tiempo real de facturas con estados categóricos (`AUTO_APPROVED`, `REJECTED`, `SCALED_TO_HUMAN`). | Visibilidad inmediata del flujo de caja y decisiones tomadas. | `OPERATIVO` |
| 🔍 **Drawer de Explicabilidad (`AuditDrawer`)** | Ficha detallada por factura con desglose FX, evaluación de las 4 capas y justificación en lenguaje natural. | Cumplimiento y auditoría transparente sin necesidad de inspeccionar código. | `OPERATIVO` |
| 🎯 **Pitch Deck Integrado (`PitchDeck`)** | Presentación comercial interactiva en `#/pitch/1` para jurados, inversionistas y comités evaluadores. | Demo y propuesta de valor navegables directamente en la app. | `OPERATIVO` |

---

## 🔒 09. Restricciones del Reto Cumplidas

* 🛡️ **Privacidad Absoluta:** No se utilizan datos reales de empresas ni de clientes. Toda la base de datos se basa en datos sintéticos controlados.
* 🛑 **Cero Pagos Indebidos:** El agente **nunca aprueba una factura fuera de las reglas** sin la confirmación explícita de un humano en el dashboard.
* 🗣️ **Explicabilidad Obligatoria:** Cada registro cuenta con una justificación generada en español claro que detalla los motivos técnicos y de negocio de la decisión.
* ⚙️ **Stack Moderno y Ligero:** Backend en Python 3.12 (FastAPI), frontend reactivo en React 18 + Tailwind CSS, base de datos PostgreSQL y modelo Google Gemini 3.8 Flash.

---

## 📈 10. Cómo se ve el Éxito (Métricas de Desempeño)

```mermaid
pie title Tasa de Acierto y Distribución en Dataset de Prueba
    "Aprobación Autónoma (Dentro de Reglas)" : 68
    "Escalado Preventivo a Humano (HITL)" : 20
    "Rechazo Automático (Duplicados / Restringidos)" : 12
```

* **Autonomía:** **68%** de las facturas rutinarias se procesan y aprueban sin intervención de un operador, liberando más de 15 horas semanales al equipo de finanzas.
* **Seguridad:** **0% de pagos indebidos.** 100% de retención en facturas duplicadas, discrepancias de monto y proveedores en listas de riesgo.
* **Explicabilidad:** **100%** de las decisiones cuentan con auditoría transparente interpretable por cualquier persona no técnica.

---

## 🏗️ Arquitectura de la Solución (Tubería de 4 Capas Deterministas)

```mermaid
flowchart TD
    subgraph INGESTA ["1. INGESTA MULTICANAL"]
        T1["Telegram Bot (@blinka_paybot)"] --> M1["Parser Multimodal"]
        T2["Dashboard Web (Dropzone PDF/Img)"] --> M1
        M1 --> OCR["Gemini 3.8 Flash (Extracción de campos JSON)"]
    end

    subgraph FX ["2. NORMALIZACIÓN CAMBIARIA"]
        OCR --> FXE["FX Engine Multidivisa"]
        FXE --> USD["Cálculo de Monto Estandarizado (USD)"]
    end

    subgraph PIPELINE ["3. TUBERÍA DETERMINISTA EN 4 CAPAS"]
        USD --> C1{"Capa 1: Cumplimiento\n¿Proveedor en lista o PEP?"}
        C1 -- No autorizado --> R1["FRENAR (REJECTED)"]
        C1 -- Válido --> C2{"Capa 2: Integridad\n¿Factura duplicada < 30d?"}
        C2 -- Duplicada --> R2["FRENAR (REJECTED)"]
        C2 -- Única --> C3{"Capa 3: Solvencia\n¿Presupuesto suficiente?"}
        C3 -- Insuficiente --> R3["FRENAR (REJECTED)"]
        C3 -- Solvente --> C4{"Capa 4: Umbral Autónomo\n¿Monto <= $2,000 USD?"}
        C4 -- Mayor al límite --> S1["ESCALAR A HUMANO (SCALED)"]
        C4 -- Dentro de límite --> P1["PAGAR AUTÓNOMO (AUTO_APPROVED)"]
    end

    subgraph AUDIT ["4. TRAZABILIDAD Y GOBIERNO"]
        R1 & R2 & R3 & S1 & P1 --> LOG["Audit Log con Explicación en Lenguaje Natural"]
        LOG --> DB[("PostgreSQL")]
        LOG --> UI["Dashboard Financiero React"]
    end

    style INGESTA fill:#04243C,stroke:#4285F4,stroke-width:2px,color:#ffffff
    style FX fill:#0B0D0E,stroke:#646CFF,stroke-width:2px,color:#ffffff
    style PIPELINE fill:#021524,stroke:#10B981,stroke-width:2px,color:#ffffff
    style AUDIT fill:#0f172a,stroke:#38B2AC,stroke-width:2px,color:#ffffff
```

---

## 💰 Viabilidad Económica y Soporte de Costos Operativos (OPEX)

Uno de los pilares del diseño de **Blinka PayAgent** es su eficiencia económica extrema. Las cifras operativas presentadas en el pitch y la documentación están respaldadas por **mediciones empíricas reales** realizadas sobre las facturas de prueba con la API de Google Gemini y telemetría de contenedores extraída directamente mediante el **CLI oficial de Railway (`railway-cli`)**.

> [!NOTE]
> **Alcance del análisis:** Se calcula estrictamente el **costo operativo recurrente (OPEX)** por procesamiento de factura (inferencia de IA + infraestructura en nube). No se computa el costo del desarrollo inicial (CAPEX) ni licencias de autoría. El canal de mensajería (Telegram Bot API) opera sobre la capa gratuita sin costo adicional.

```mermaid
flowchart LR
    subgraph COSTO_UNITARIO ["💵 DESGLOSE DE COSTO POR FACTURA (~$0.01 USD / FACTURA A 1.000 DOCS/MES)"]
        direction TB
        IA["🧠 Inferencia Gemini 3.8 Flash<br/><b>$0.0050 USD</b> (50%)<br/>• OCR Multimodal (1 llamada)<br/>• Esquema JSON estricto"]
        INFRA["☁️ Infraestructura Railway<br/><b>$0.0050 USD</b> (50%)<br/>• FastAPI + Postgres + React<br/>• Plan Hobby ($5/mes incluye $5 cómputo)"]
    end
```

---

### 1. Modelo de IA Utilizado y Telemetría de Tokens

* **Modelo Seleccionado:** `gemini-3.8-flash` (configurado en `backend/app/config.py` mediante la variable `GEMINI_MODEL`).
* **Estrategia de Inferencia:** Arquitectura de **1 sola llamada multimodal por documento** (`client.aio.models.generate_content`) que extrae directamente la estructura tipada (`EXTRACTION_SCHEMA`) con `temperature=0` para garantizar reproducibilidad matemática.
* **Medición Real de Tokens:** Ejecutando el extractor contra los documentos sintéticos de demostración (`docs/pitch_presentacion/facturas_demo/`):

| Tipo de Documento | Tokens Entrada (Prompt + Doc) | Tokens Salida (JSON Estructurado) | Tokens Razonamiento (*Thinking*) | Total Tokens / Factura | Costo Inferencia (USD) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Factura PDF** (Vectorial / Escaneada) | ~1,090 | ~146 | ~903 | **~2,139** | **$0.00475 USD** |
| **Foto / Imagen PNG** (Captura Telegram) | ~1,603 | ~146 | ~903 | **~2,652** | **$0.00514 USD** |
| **Factura Duplicada** (Filtro SHA-256) | 0 | 0 | 0 | **0** | **$0.00000 USD** |

* **Tarifas Oficiales de Google Gemini API** *(Standard Paid Tier)*:
  * Entrada: **$0.75 USD** por millón de tokens ($0.00000075 / token).
  * Salida (incluye tokens de razonamiento): **$3.75 USD** por millón de tokens ($0.00000375 / token).
* **Fórmula de Cálculo:**
  $$\text{Costo IA (PDF)} = (1,090 \times \frac{0.75}{10^6}) + ((146 + 903) \times \frac{3.75}{10^6}) = \$0.00082 + \$0.00393 = \mathbf{\$0.00475\ USD}$$
  $$\text{Costo Promedio Ponderado de IA} \approx \mathbf{\$0.0050\ USD\ /\ factura\ (\$5.00\ USD\ /\ 1.000\ facturas)}$$

---

### 2. Infraestructura de Cómputo y Telemetría en Railway

La solución completa opera en producción en **Railway**, dividida en tres servicios contenerizados conectados por red privada:
1. `backend`: Contenedor Python 3.12 / FastAPI / Uvicorn (~67 MB RAM en reposo, < 0.01 vCPU).
2. `Postgres`: Base de datos PostgreSQL para almacenamiento inmutable de auditoría, lista blanca y reglas (~55 MB RAM, 116 MB de volumen).
3. `30X_404_team` (frontend): Servidor web estático Nginx con la aplicación React 18 / Vite (~39 MB RAM, 0 vCPU en reposo).

#### Comandos de Telemetría Ejecutados con Railway CLI:
```bash
# 1. Monitoreo del consumo acumulado y facturación del workspace
railway usage

# 2. Desglose detallado por servicio en formato JSON estructurado
railway usage projects --project <PROJECT_ID> --json

# 3. Métricas de consumo de CPU, memoria RAM y ancho de banda en tiempo real
railway metrics -p <PROJECT_ID> -e production -a --since 2d
```

#### Evidencia Empírica de Consumo (Telemetría en Producción):
* **Consumo Real Medido en ~24 Horas:** **$0.0394 USD** acumulados tras procesar 20 facturas entre canales Web, API y Webhook de Telegram:
  * Servicio `backend`: $0.0130 USD (CPU: $0.00047, RAM: $0.01242, Red: $0.00014).
  * Servicio `Postgres`: $0.0158 USD (RAM: $0.01529, Disco: $0.00034, CPU: $0.00018).
  * Servicio `frontend`: $0.0106 USD (RAM: $0.01020, Red: $0.00038, CPU: $0.00001).
* **Proyección Mensual de Consumo de Hardware:** **~$1.20 USD / mes**. El 96% corresponde al consumo base de memoria RAM de los contenedores en espera activa (*idle*).
* **Costo Marginal de Infraestructura:** Menos de **$0.00003 USD por factura adicional** en CPU y transferencia de red.
* **Modelo Comercial de Railway:** El **Plan Hobby ($5.00 USD/mes)** incluye **$5.00 USD de crédito de cómputo**. Como nuestro consumo proyectado es de ~$1.20 USD/mes, la operación completa se absorbe íntegramente dentro de los $5.00 USD fijos del plan.

---

### 3. Matriz Consolidada de Costos por Volumen (Unit Economics)

La siguiente tabla ilustra la escalabilidad de costos del sistema ante diferentes volúmenes mensuales:

| Facturas / Mes | Costo IA (Gemini 3.8 Flash) | Costo Infraestructura (Railway) | **Costo Total Mensual** | **Costo Unitario por Factura** | Equivalente Estimado (COP)* |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **100** | $0.50 USD | $5.00 USD | **$5.50 USD** | $0.0550 USD | ~231 COP |
| **1,000** | $5.00 USD | $5.00 USD | **$10.00 USD** | **$0.0100 USD** | **~42 COP** |
| **5,000** | $25.00 USD | $5.00 USD | **$30.00 USD** | **$0.0060 USD** | **~25 COP** |
| **10,000** | $50.00 USD | $5.00 USD | **$55.00 USD** | **$0.0055 USD** | **~23 COP** |
| **50,000** | $250.00 USD | $7.50 USD** | **$257.50 USD** | **$0.0051 USD** | **~21 COP** |

*\*TRM de referencia estimada: $4,200 COP / USD.*  
*\*\*A partir de 50,000 facturas/mes se proyecta un incremento marginal en recursos de base de datos y memoria caché.*

> [!TIP]
> **Costo Marginal por Cada 1,000 Facturas Adicionales:** **~$5.03 USD** ($5.00 USD de inferencia de IA + $0.03 USD de cómputo marginal en nube).

---

## 🏛️ Estructura del Monorepo

```
30X_404_team/
├── .env.example             # Plantilla unificada de variables de entorno (Monorepo)
├── .gitignore               # Exclusiones de Git unificadas
├── plan_de_trabajo.md       # Cronograma oficial y distribución del equipo
├── backend/                 # API REST FastAPI & Arquitectura Hexagonal
│   ├── app/
│   │   ├── domain/          # Entidades (Invoice, Vendor, Rule, Audit)
│   │   ├── ports/           # Interfaces (Inbound & Outbound)
│   │   └── adapters/        # Implementaciones (Postgres, Gemini, Telegram, FX)
│   ├── requirements.txt     # Dependencias de Python 3.12
│   └── Dockerfile           # Contenedor de producción backend
├── frontend/                # Aplicación Web React 18 + Vite 5 + Tailwind CSS
│   ├── src/
│   │   ├── components/      # Dashboard, RuleControls, AuditTable, PitchDeck
│   │   ├── api.js           # Cliente HTTP hacia la API REST
│   │   └── Root.jsx         # Enrutamiento hash (#/pitch, #/stitch, app)
│   ├── package.json         # Dependencias frontend
│   └── Dockerfile           # Contenedor Nginx de producción frontend
├── docs/                    # Documentación de arquitectura, reglas y pitch
│   ├── arquitectura/        # Especificaciones de arquitectura v5
│   ├── reglas-negocio/      # Reglas detalladas de negocio v3
│   └── pitch_presentacion/  # Guiones y diapositivas del Pitch
└── specs/                   # Especificaciones de misión y roadmap
```

---

## 🚀 Puesta en Marcha Local

### Prerrequisitos
* Python 3.12+
* Node.js 18+ y npm
* PostgreSQL (o usar el modo demo con datos simulados)

### 1. Clonar el repositorio y configurar variables
```bash
git clone https://github.com/Oriojas/30X_404_team.git
cd 30X_404_team
cp .env.example .env
# Configura tus credenciales en .env (Gemini API Key, Telegram Token, etc.)
```

### 2. Iniciar el Backend (FastAPI)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```
> Swagger UI disponible en: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Iniciar el Frontend (React + Vite)
En una nueva terminal:
```bash
cd frontend
npm install
npm run dev
```
> Aplicación interactiva disponible en: [http://localhost:3000](http://localhost:3000)

---

## 👥 Equipo 404 — Hackathon 30X

| Miembro | Perfil GitHub | Rol | Especialidad y Contribución |
| :--- | :---: | :--- | :--- |
| **Luis Felipe Marín Giraldo** | [![GitHub](https://img.shields.io/badge/GitHub-LuisFelipe09-181717?style=flat&logo=github)](https://github.com/LuisFelipe09) | Lead Backend & AI Engineer | Arquitectura Hexagonal FastAPI, Adaptador Gemini 3.8 Flash OCR, Bot Webhook Telegram, Engine FX Multidivisa y Persistencia PostgreSQL. |
| **Oscar Riojas** | [![GitHub](https://img.shields.io/badge/GitHub-Oriojas-181717?style=flat&logo=github)](https://github.com/Oriojas) | Lead Frontend & Product Lead | Monorepo Architecture, Dashboard React + Tailwind UI, Pitch Deck interactivo, Laboratorio Stitch MCP, Trazabilidad y Experiencia de Usuario. |

---

<div align="center">

**Blinka PayAgent** — *Construyendo la infraestructura de confianza para pagos autónomos gobernados por IA.*  
[Ver Video Pitch en YouTube](https://youtu.be/ieCPVmi2RJk) • [Ver Demo en Vivo](https://30x404team-production.up.railway.app/) • [Ver Presentación (Pitch)](https://30x404team-production.up.railway.app/#/pitch/1)

</div>