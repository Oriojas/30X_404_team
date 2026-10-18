# 🎬 Blinka PayAgent — Presentación y Guion Oficial V5 (Casos Reales Grabados + Demo al Final)

> **Documento de Trabajo Oficial para el Hackathon 30X (2da Edición)**  
> **Equipo 404:** Oscar Riojas & Luis Felipe Marín Giraldo  
> **Entregables:** Repositorio GitHub (`Oriojas/30X_404_team`) | Demo en Vivo (`30x404team-production.up.railway.app`)  
> **Duración Máxima del Pitch:** 3 Minutos (180 Segundos)

---

## 📌 1. Qué cambia frente a la V4 (Alineación con las Grabaciones Reales)

En esta versión V5, ajustamos el guion y el orden visual para sincronizarlo al 100% con los **videos reales grabados en producción**:

| # | Elemento en V4 | Ajuste Oficial V5 | Razón del Cambio |
| :---: | :--- | :--- | :--- |
| **1** | Demo en Bloque 3 (mitad del video). | **Demo al final del pitch (Bloque 5 · 1:55 – 2:45).** | Permite exponer primero el valor comercial, la arquitectura, los costos y el impacto antes de entrar a la evidencia en vivo. |
| **2** | Factura hipotética de AWS Cloud en PDF. | **Factura real de COMCEL S.A. (#13489CAV) por Telegram Bot.** | $173,360 COP normalizados a **$41.28 USD** (TRM 4,200). Aprobada autónomamente (`AUTO_APPROVED`). Grabado en video de celular. |
| **3** | Rechazo por lista OFAC simulado. | **Documento ilegible / Proveedor Desconocido (#SIN_NUMERO).** | El agente frena preventivamente por `INTEG-03` (confianza 0%) y `HITL-02` (proveedor no registrado), escalando a `SCALED_TO_HUMAN`. |
| **4** | Aprobación humana del biométrico. | **Decisión Humana y Rechazo Manual del CFO (`HUMAN_REJECTED`).** | El CFO revisa la factura escalada en el dashboard y pulsa **"Rechazar Pago"** con la nota: *"Se rechaza por no ser legible"*, demostrando gobierno total. |
| **5** | Costos en Slide 6 (aislada al final). | **Costos en Slide 5 (antes del impacto y del demo).** | Flujo narrativo continuo: Problema ➔ Solución ➔ Arquitectura ➔ Costos ➔ Impacto ➔ **Demo en Vivo** ➔ Cierre. |

---

## 📋 2. Estructura de las Diapositivas (Deck V5)

### 🖼️ Slide 1: Portada & Propuesta de Valor (0:00 – 0:15)
* **Título:** Blinka PayAgent — *Gobernanza financiera y decisiones autónomas de pago*.
* **Subtítulo:** Cero pagos indebidos, normalización multidivisa y trazabilidad total por ~$0.01 USD por factura.
* **Visual:** Mockup corporativo mostrando la interacción por Telegram Bot y el Dashboard institucional.
* **Footer:** Reto Blinka | Hackathon 30X | Equipo 404 | Desplegado en Railway.

---

### 🖼️ Slide 2: El Problema Real (La Ilusión del Control) (0:15 – 0:30)
* **Concepto Clave:** *Las cuentas grandes están bajo control; las facturas de servicios, imprevistos y divisas dispersas paralizan la tesorería.*
* **01. Fricción en Facturas de Servicios e Imprevistos:** Cuentas de telefonía, reparaciones o contratistas nuevos que rebotan entre correos buscando aprobación.
* **02. Fricción Multidivisa en LatAm:** Pagos en COP, MXN, BRL o EUR liquidados desde cuentas en USD con sobrecostos cambiarios.
* **03. Riesgo de Pagos Indebidos:** Facturas duplicadas o documentos ilegibles que se aprueban por fatiga administrativa.

---

### 🖼️ Slide 3: La Solución — Gobernanza Ejecutada (0:30 – 0:50)
* **Concepto:** Un agente inteligente que lee documentos multimodales, evalúa políticas en milisegundos y emite una decisión categorizada con explicabilidad de caja blanca.
* **Matriz de Decisiones:**
  * 🟢 **`AUTO_APPROVED` (Pagar):** Proveedor verificado, dentro de presupuesto y bajo el umbral autónomo (< $2,000 USD).
  * 🔴 **`REJECTED` (Frenar):** Cobro duplicado (< 30 días) o coincidencia en lista restrictiva (SARLAFT/OFAC).
  * 🟠 **`SCALED_TO_HUMAN` (Escalar):** Supera umbral, proveedor nuevo o documento con inconsistencias.
  * 🔵 / 🔴 **`HUMAN_APPROVED` / `HUMAN_REJECTED`:** Decisión humana registrada en 1 clic con bitácora inmutable.
* **Gobernanza:** *"El agente decide y audita; no mueve dinero real sin autorización."*

---

### 🖼️ Slide 4: Arquitectura Hexagonal y Tubería de 4 Capas (0:50 – 1:10)
* **Core Desacoplado (FastAPI en Railway):**
  1. *Percepción:* Ingesta multicanal (Telegram Bot activo / Webhook REST) con **Google Gemini 3.8 Flash** (1 sola llamada multimodal por factura).
  2. *Normalización:* FX Engine estandariza a USD según tasa oficial.
  3. *Tubería Determinista (Python puro):*
     * **Capa 1 Compliance:** Listas restrictivas (OFAC/ONU), cuentas bancarias y PEP.
     * **Capa 2 Integridad:** Hash SHA-256 para duplicados (< 30 días) y confianza OCR ≥ 85%.
     * **Capa 3 Solvencia:** Presupuesto mensual y saldo disponible.
     * **Capa 4 Gobierno HITL:** Límite autónomo de $2,000 USD y verificación de proveedores.
  4. *Audit Logger:* Explicabilidad en lenguaje natural y persistencia en PostgreSQL.

---

### 🖼️ Slide 5: Viabilidad Financiera & Costos Operativos (1:10 – 1:35)
* **Mensaje Principal:** *Operar el agente cuesta ~$0.005 USD de IA por factura y ~$10 USD al mes para 1,000 facturas completas.*
* **Telemetría Real:**
  * **IA (Gemini 3.8 Flash):** ~$0.005 USD por documento (2,139 tokens PDF / 2,652 tokens imagen). Facturas duplicadas: **$0.00 IA** (filtro SHA-256).
  * **Infraestructura (Railway):** 3 servicios activos (FastAPI + Postgres + React) consumen **$0.039 USD en 24h** (~$1.20 USD/mes proyectado, 100% absorbido por el Plan Hobby de $5 USD/mes).
  * **Unit Economics:** 1,000 facturas/mes = **$10.00 USD total (~$0.010 USD / ~42 COP por factura)**. Cada 1,000 facturas adicionales suman solo **~$5.03 USD**.

---

### 🖼️ Slide 6: Impacto de Negocio y Métricas (1:35 – 1:55)
* **~90%** de reducción en carga manual contable.
* **0** pagos fuera de reglas (Garantía de cero pagos indebidos).
* **5+** divisas normalizadas automáticamente (COP, MXN, EUR, BRL, ARS ➔ USD).
* **168** pruebas unitarias y de integración activas (100% aprobadas).
* 🌐 `30x404team-production.up.railway.app` · 📦 `github.com/Oriojas/30X_404_team`

---

### 🖼️ Slide 7 (Final): Demostración en Vivo en Producción (1:55 – 2:45)
* **Muestra del Audit Log con los casos reales grabados:**
  1. `COMCEL S.A.` (#13489CAV): $173,360 COP ➔ **$41.28 USD** ➔ 🟢 `AUTO_APPROVED` vía Telegram.
  2. `PROVEEDOR_DESCONOCIDO` (#SIN_NUMERO): $0.00 USD ➔ 🟠 `SCALED_TO_HUMAN` (Freno preventivo por ilegibilidad `INTEG-03` y proveedor no registrado `HITL-02`).
  3. `PROVEEDOR_DESCONOCIDO` (#SIN_NUMERO): $0.00 USD ➔ 🔴 `HUMAN_REJECTED` (Rechazado manualmente por el CFO en el dashboard con nota *"Se rechaza por no ser legible"*).

---

## 🎙️ 3. Guion Cronometrado para el Video Pitch (3 Minutos / 180 Segundos)

### ⏱️ Bloque 1: Apertura & El Problema Real (0:00 – 0:30 · 30s)
*(En cámara o con Slide 1 y Slide 2 en pantalla · Tono seguro y conversacional)*

> *"En cualquier empresa, las cuentas grandes están bajo control: nómina, servidores o arriendos. Finanzas les hace un seguimiento milimétrico.*
> 
> *El verdadero dolor de cabeza ocurre en los gastos imprevistos y facturas recurrentes de servicios: la cuenta de telefonía, un mantenimiento de urgencia o un contratista nuevo. Llegan en monedas locales como pesos colombianos o mexicanos, rebotan de correo en correo buscando quién las autorice, y muchas veces se pagan tarde o se duplican por falta de trazabilidad.*
> 
> *Para resolverlo creamos **Blinka PayAgent**: un agente de gobernanza financiera que revisa, decide y audita cada factura en segundos con cero pagos indebidos."*

---

### ⏱️ Bloque 2: Solución & Arquitectura Determinista (0:30 – 1:05 · 35s)
*(Transición a Slide 3 y Slide 4 en pantalla)*

> *"¿Cómo funciona? El usuario o proveedor simplemente envía la factura por nuestro bot de Telegram o por el portal web.*
> 
> *Nuestro adaptador multimodal con **Gemini 3.8 Flash** realiza una única llamada de extracción y devuelve un JSON estructurado. De inmediato, nuestro motor FX normaliza la divisa a dólares y entra a una tubería determinista de cuatro capas en Python puro:*
> 
> *Primero: Compliance contra listas SARLAFT y OFAC.*
> *Segundo: Integridad y descarte de cobros duplicados.*
> *Tercero: Solvencia y presupuesto mensual.*
> *Y cuarto: Gobierno con límite autónomo de 2,000 dólares.*
> 
> *La IA solo lee; la decisión la toma código determinista sin alucinaciones, desplegado en arquitectura hexagonal sobre FastAPI en Railway."*

---

### ⏱️ Bloque 3: Costos Operativos por Factura (1:05 – 1:35 · 30s)
*(Slide 5 en pantalla · Enfoque en los datos de Railway y Gemini)*

> *"¿Cuánto cuesta operar esta solución? Medimos el consumo real en producción con el CLI de Railway y la API de Gemini.*
> 
> *Cada documento consume apenas medio centavo de dólar de IA. Toda nuestra infraestructura —con backend, base de datos PostgreSQL y frontend— consume apenas 3.9 centavos al día, unos $1.20 dólares al mes, totalmente cubiertos por el plan Hobby de 5 dólares de Railway.*
> 
> *Esto significa que procesar mil facturas al mes cuesta tan solo **diez dólares en total**: un centavo de dólar por factura, unos 42 pesos colombianos. Y cada mil facturas adicionales agregan solo cinco dólares."*

---

### ⏱️ Bloque 4: Impacto de Negocio (1:35 – 1:55 · 20s)
*(Slide 6 en pantalla)*

> *"El impacto es contundente: reducimos cerca de un 90% la carga manual de tesorería, normalizamos automáticamente más de cinco divisas latinoamericanas y garantizamos cero pagos fuera de reglas: ante la menor inconsistencia, el agente frena preventivamente y escala."*

---

### ⏱️ Bloque 5: Demostración en Vivo en Producción (1:55 – 2:45 · 50s)
*(Entran los clips de video grabados por Oscar · Edición dinámica con audio sincronizado)*

* **[1:55 - 2:15] Caso 1 — Factura de Comcel por Telegram (`AUTO_APPROVED`):**
  *(Clip del celular mostrando la interacción en Telegram Bot)*
  > *"Veámoslo en vivo. Aquí enviamos desde el celular por Telegram la factura mensual de servicios de Comcel por 173,360 pesos colombianos. El agente procesa la imagen, el FX Engine la convierte a $41.28 dólares y confirma que Comcel es un proveedor autorizado en lista permitida y que no supera el límite autónomo. En cuestión de segundos, el bot responde confirmando la aprobación automática: `AUTO_APPROVED`."*

* **[2:15 - 2:30] Caso 2 — Freno Preventivo por Ilegibilidad (`SCALED_TO_HUMAN`):**
  *(Clip del Dashboard Web mostrando la tabla de auditoría)*
  > *"Ahora vemos el Dashboard en Railway. La factura de Comcel ya está registrada con su justificación de caja blanca. Pero ¿qué ocurre si recibimos un documento ilegible o de un proveedor no registrado? El agente detecta cero confianza en la extracción y aplica las reglas `INTEG-03` y `HITL-02`: frena el pago de inmediato y lo escala a revisión humana: `SCALED_TO_HUMAN`."*

* **[2:30 - 2:45] Caso 3 — Decisión Humana del CFO y Rechazo Inmediato (`HUMAN_REJECTED`):**
  *(Clip mostrando el Drawer lateral y el clic en Rechazar Pago)*
  > *"Como CFO, abro el detalle de la factura escalada, leo la explicación del agente y tomo el control: hago clic en 'Rechazar Pago' agregando la nota 'Se rechaza por no ser legible'. La factura cambia al instante a `HUMAN_REJECTED`, guardando la auditoría inmutable de quién decidió, cuándo y por qué."*

---

### ⏱️ Bloque 6: Cierre Oficial & Repositorio (2:45 – 3:00 · 15s)
*(En cámara o con Slide 6/7 de fondo mostrando URLs)*

> *"Blinka PayAgent ya está desplegado y funcionando en producción en Railway, y todo nuestro código está abierto en GitHub respaldado por 168 pruebas automatizadas.
> Somos el Equipo 404 para el Reto Blinka. ¡Muchas gracias!"*

---

## 📊 4. Matriz de Concordancia de la Demostración

Para facilitar la edición del video, esta es la correspondencia exacta entre tus clips grabados y la justificación mostrada:

| # | Canal Grabado | Documento / Proveedor | Monto | Estado en Pantalla | Reglas Disparadas | Justificación Caja Blanca en Audit Log |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | Telegram Bot (Video Celular) | **COMCEL S.A.** (#13489CAV) | 173,360 COP (**$41.28 USD**) | 🟢 `AUTO_APPROVED` | — | *Pago aprobado automáticamente: $41.28 USD (173,360 COP a tasa 4,200.00) dentro del límite autónomo, proveedor activo en la lista permitida, sin alertas de cumplimiento y saldo suficiente.* |
| **2** | Dashboard Web (Subida) | **PROVEEDOR_DESCONOCIDO** (#SIN_NUMERO) | $0.00 USD | 🟠 `SCALED_TO_HUMAN` | `INTEG-03`<br/>`HITL-02` | *Pago de $0.00 USD escalado a revisión humana: [INTEG-03] Lectura de factura ambigua o ilegible (confianza 0%). Requiere revisión. [HITL-02] Beneficiario fuera de la lista permitida.* |
| **3** | Dashboard Web (Drawer CFO) | **PROVEEDOR_DESCONOCIDO** (#SIN_NUMERO) | $0.00 USD | 🔴 `HUMAN_REJECTED` | `HITL-02` | *Rechazado manualmente por CFO Demo desde el dashboard el 2026-10-18 01:02 UTC. Nota: Se rechaza por no ser legible.* |
