# 🎬 Blinka PayAgent — Presentación y Guion Oficial V3 (Con Escenario del Lector Biométrico)

> **Documento de Trabajo para el Hackathon 30X (2da Edición)**
> **Equipo 404:** Oscar Riojas & Luis Felipe Marín Giraldo
> **Entregables:** Repositorio GitHub (`Oriojas/30X_404_team`) | Demo en Vivo (`30x404team-production.up.railway.app`)

---

## 📌 1. Análisis del Nuevo Escenario de Apertura

En la última actualización táctica, identificaste la forma más humana, empática y convincente de iniciar el pitch comercial: **el caso del imprevisto operativo (*Long-Tail / Ad-Hoc Spend*)**.

### 💡 ¿Por qué este escenario transforma el Pitch?
1. **Rompe la ilusión del control:** En las empresas, los costos grandes y recurrentes (nube, nómina, arriendo) ya están bajo control. El verdadero caos financiero ocurre en los gastos no planificados.
2. **Ilustra el calvario de la aprobación manual:** Muestra cómo una factura de emergencia de un proveedor nuevo empieza a rebotar de correo en correo y de chat en chat porque nadie sabe quién la autorizó ni cómo categorizarla.
3. **Muestra el costo de oportunidad real:** No es solo el retraso administrativo: pagar fuera de fecha destruye la relación comercial con el único técnico que te sacó del apuro. Seis meses después el equipo vuelve a fallar y el proveedor se niega a prestar el servicio.
4. **Demuestra el valor de Blinka PayAgent:** Cómo el agente recibe la foto de esa cuenta de cobro informal por Telegram, identifica que es un proveedor nuevo, la escala inmediatamente con una notificación clara al CFO y permite aprobarla en 1 clic desde el Dashboard o Telegram, manteniendo la gobernanza y asegurando la continuidad del negocio.

---

## 📋 2. Estructura de la Presentación Deck V3 (6 Diapositivas)

### 🖼️ Slide 1: Portada & Propuesta de Valor
- **Título Principal:** Blinka PayAgent — *Agentes IA de decisión de pagos con gobernanza financiera*.
- **Subtítulo:** Cero pagos indebidos, conversión de divisas sin sobrecosto y trazabilidad total.
- **Visual Principal:** Mockup de teléfono en Telegram procesando la cuenta de cobro de emergencia del servicio biométrico (`SCALED_TO_HUMAN` ➔ `HUMAN_APPROVED`) y la factura recurrente de AWS Cloud (`AUTO_APPROVED`).
- **Footer:** Reto Blinka | Hackathon 30X | Equipo 404 | Desplegado en Railway.

---

### 🖼️ Slide 2: El Problema Real (La Ilusión del Control)
- **Concepto:** Las cuentas grandes están bajo control, pero los gastos imprevistos y la fricción de divisas paralizan la operación.
- **01. El Calvario de los Imprevistos (*Ad-Hoc Spend*):** Un sábado falla el lector biométrico. Se llama a un técnico de urgencia, pero su factura de proveedor nuevo se pierde en correos buscando aprobación, dañando la relación comercial.
- **02. Fricción Multidivisa en LatAm:** Facturas en COP, MXN, EUR, BRL o ARS pagadas desde cuentas corporativas en USD con altas comisiones cambiarias (*FX markups*).
- **03. Riesgo de Pagos Indebidos:** Facturas duplicadas en menos de 30 días o proveedores no verificados en SARLAFT que se aprueban por falta de trazabilidad.

---

### 🖼️ Slide 3: La Solución — Gobernanza Financiera Ejecutada
- **Concepto:** Un agente conectado a Telegram lee facturas multimodales con Gemini 1.5 Flash, aplica el motor de reglas determinista de Blinka y registra la decisión en tiempo real.
- **Matriz de Decisiones de 4 Estados:**
  1. 🟢 **`AUTO_APPROVED` (Pagar):** Proveedor verificado, dentro del presupuesto y del límite autónomo (< $2,000 USD).
  2. 🔴 **`REJECTED` (Frenar):** Cobro duplicado (< 30 días) o coincidencia en lista restrictiva (SARLAFT/OFAC).
  3. 🟠 **`SCALED_TO_HUMAN` (Escalar):** Supera el umbral, es un proveedor nuevo o saldo insuficiente.
  4. 🔵 **`HUMAN_APPROVED` (Aprobado en Dashboard):** El CFO revisa la justificación y autoriza la factura escalada en 1 clic.
- **Nota Clave para el Jurado:** *"El agente decide, valida y registra con explicabilidad en lenguaje natural; no ejecuta pagos reales ni mueve dinero sin autorización."*

---

### 🖼️ Slide 4: Arquitectura Hexagonal y Pipeline de 4 Capas
- **Esquema de Desacoplamiento:**
  - **Entradas (Adaptadores):** Telegram (MVP activo), preparado para WhatsApp o Email sin alterar el Core.
  - **Core del Agente (FastAPI):**
    1. *Gemini 1.5 Flash:* OCR Multimodal y estructuración JSON.
    2. *FX Engine:* Normalización de divisas a USD a tasa oficial ($0.00 FX Markup).
    3. *Reglas Blinka:* Pipeline determinista en código Python puro (sin alucinaciones de LLM).
    4. *Audit Logger:* Generación de explicaciones en lenguaje natural.
  - **Persistencia / UI:** Base de datos PostgreSQL nativa en Railway y Dashboard React.
- **Pipeline Determinista de 4 Capas:**
  - *Capa 1 Compliance:* SARLAFT, OFAC, ONU, listas restrictivas y NIT.
  - *Capa 2 Integridad:* Detección de duplicados (< 30 días) y confianza OCR ≥ 85%.
  - *Capa 3 Solvencia:* Presupuesto del periodo y saldo disponible en Blinka.
  - *Capa 4 Gobierno HITL:* Límite autónomo de $2,000 USD y verificación de proveedores nuevos.

---

### 🖼️ Slide 5: Demo en Vivo & Audit Log
- **Muestra del Dashboard en Producción:** Visualización de la tabla interactiva de auditoría en `30x404team-production.up.railway.app`.
- **Casos de Prueba Reales Representados:**
  - **Reparación Biométrico (450,000 COP / $107.14 USD):** Proveedor nuevo ➔ `SCALED_TO_HUMAN` ➔ Aprobado por el CFO ➔ `HUMAN_APPROVED`.
  - **AWS Cloud Services (1,200,000 COP / $285.71 USD):** Proveedor verificado y presupuesto disponible ➔ `AUTO_APPROVED`.
  - **AWS Cloud Services (1,200,000 COP / $285.71 USD):** Reenvío de factura duplicada ➔ `REJECTED` por regla `INTEG-01`.
  - **Logística Express MX (117,000 MXN / $6,000.00 USD):** Excede umbral de $2,000 USD ➔ `SCALED_TO_HUMAN` ➔ Aprobación en 1 clic.

---

### 🖼️ Slide 6: Impacto de Negocio y Viabilidad
- **Métricas de Impacto:**
  - **~90%** de reducción en carga manual de revisión.
  - **5+** divisas normalizadas automáticamente (COP, MXN, EUR, BRL, ARS ➔ USD).
  - **0** pagos fuera de reglas (Garantía de cero pagos indebidos).
  - **1** sola llamada de inferencia a Gemini por factura (Eficiencia técnica y costos mínimos).
- **Despliegue y Código:**
  - 🌐 Demo en vivo: `30x404team-production.up.railway.app`
  - 📦 Código abierto: `github.com/Oriojas/30X_404_team`

---

## 🎙️ 3. Guion Cronometrado para el Video Pitch (3 Minutos / 180 Segundos)

### ⏱️ Bloque 1: El Gancho Comercial — El Lector Biométrico del Sábado (0:00 – 0:42)
* **[0:00 - 0:15] La Ilusión del Control (En cámara / Tono conversacional seguro):**
  > *"En cualquier empresa, las cuentas grandes y recurrentes están bajo control: la nómina, el arriendo, los servidores en la nube. Finanzas les hace un seguimiento milimétrico.*
  > *Pero… ¿qué pasa un sábado a las ocho de la mañana cuando se daña el lector biométrico de la oficina y nadie puede entrar a trabajar?"*

* **[0:15 - 0:30] La Fricción Operativa (En cámara / Tono empático y expresivo):**
  > *"Llamas de urgencia a un técnico de emergencia. Llega, lo repara en una hora, te envía una cuenta de cobro y se va.*
  > *Y ahí empieza el calvario: es un proveedor nuevo que no está en el sistema, el concepto es una reparación imprevista, y la factura empieza a rebotar de correo en correo y de chat en chat buscando una aprobación que nunca llega.*
  > *Pasan las semanas, la factura se paga fuera de fecha y quemaste la relación con el único técnico que te sacó del apuro. Seis meses después el lector vuelve a fallar, lo llamas… y ya no te contesta."*

* **[0:30 - 0:42] El Puente a la Solución (Transición visual a la pantalla dividida con Telegram):**
  > *"Este tipo de fricción no solo destruye relaciones comerciales: le cuesta cientos de horas al mes a los equipos de tesorería global.*
  > *Por eso creamos **Blinka PayAgent**: un agente de gobernanza financiera que convierte esa foto o PDF de Telegram en una decisión determinista, auditable y segura en segundos, sin pagos indebidos y con trazabilidad total."*

---

### ⏱️ Bloque 2: Demostración en Vivo en Producción (0:42 – 1:50)
*(Pantalla dividida: Bot de Telegram a la izquierda y Dashboard en React desplegado en Railway a la derecha)*

* **[0:42 - 1:05] Caso 1 — El Lector Biométrico y la Aprobación HITL (`HUMAN_APPROVED`):**
  > *"Veamos nuestro caso del sábado. El usuario toma una foto a la factura del técnico del biométrico y la envía por Telegram. Nuestro adaptador procesa la imagen con Gemini 1.5 Flash. El FX Engine convierte los 450,000 COP a $107 dólares. Nuestro pipeline detecta que es un 'Proveedor Nuevo' (Regla HITL-01), frena el pago preventivo y notifica al CFO.*
  > *En nuestro Dashboard web en Railway, el CFO ve la alerta, lee la explicación clara en lenguaje natural y hace clic en 'Aprobar'. La factura cambia a `HUMAN_APPROVED` y el técnico recibe su confirmación en minutos."*

* **[1:05 - 1:20] Caso 2 — Factura Recurrente Autónoma (`AUTO_APPROVED`):**
  > *"Ahora enviamos la factura mensual de AWS Cloud por 1,200,000 pesos colombianos. El agente extrae los datos, convierte el monto a $285.71 dólares, verifica que el proveedor está autorizado, que hay saldo disponible y que está dentro del límite autónomo de $2,000 USD. El resultado: `AUTO_APPROVED` automáticamente."*

* **[1:20 - 1:35] Caso 3 — Detección de Cobro Duplicado (`REJECTED`):**
  > *"¿Qué sucede si nos intentan cobrar dos veces la misma factura? Reenviamos el mismo documento. El agente consulta nuestro historial en PostgreSQL, detecta que la factura ya fue procesada en los últimos 30 días y aplica la regla `INTEG-01`, marcándola como `REJECTED` de inmediato."*

* **[1:35 - 1:50] Caso 4 — Exceso de Umbral Autónomo (`SCALED_TO_HUMAN`):**
  > *"Finalmente, enviamos una factura en euros por 3,200 EUR ($3,478 USD) de Oracle Enterprise. Dado que supera el límite autónomo de $2,000 USD, salta la regla `HITL-01` y escala el caso para revisión humana, garantizando cero pagos indebidos."*

---

### ⏱️ Bloque 3: Arquitectura Hexagonal y Seguridad (1:50 – 2:20)
*(Aparece en pantalla el diagrama de arquitectura hexagonal de `arquitectura_solucion_v4.md`)*

* **[1:50 - 2:20] Explicación Técnica (Voz en off clara y profesional):**
  > *"Construimos Blinka PayAgent con arquitectura hexagonal en FastAPI. Los adaptadores de entrada como Telegram están 100% desacoplados del Core, listos para conectar WhatsApp o correo corporativo.*
  > *Utilizamos Gemini 1.5 Flash para realizar únicamente 1 llamada de inferencia por factura para el OCR multimodal. Toda la evaluación de las 4 capas de gobernanza se ejecuta en código Python determinista, garantizando cero alucinaciones de IA y costos de inferencia mínimos."*

---

### ⏱️ Bloque 4: Impacto de Negocio, ROI y Cierre (2:20 – 3:00)
*(Visual del Dashboard completo en React mostrando todas las métricas e insignias)*

* **[2:20 - 2:45] Métricas e Impacto Comercial:**
  > *"Con Blinka PayAgent logramos un 90% de reducción en el tiempo de procesamiento manual, normalizamos más de 5 divisas latinoamericanas a dólares sin sobrecosto cambiario y eliminamos el 100% de los pagos fuera de reglas."*

* **[2:45 - 3:00] Cierre y Llamado a la Acción:**
  > *"Nuestra solución está desplegada y funcional en Railway en `30x404team-production.up.railway.app` y con el código abierto en GitHub. Somos el Equipo 404 y esto es Blinka PayAgent. ¡Muchas gracias!"*

---

## 📊 4. Matriz de Datos de Prueba para la Grabación del Demo

| # | Caso de Uso | Canal | Documento Simulado | Moneda Orig. | Monto USD | Estado Final | Regla Disparada | Justificación en Audit Log |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Reparación Lector Biométrico | Telegram / UI | `Factura_Biometrico.pdf` | $450,000 COP | **$107.14 USD** | 🔵 `HUMAN_APPROVED` | `HITL-01` | *Proveedor nuevo. Escalado a revisión y aprobado por el CFO en el dashboard.* |
| **2** | Factura Nube Recurrente | Telegram | `Factura_AWS_Cloud.pdf` | $1,200,000 COP | **$285.71 USD** | 🟢 `AUTO_APPROVED` | — | *Proveedor verificado, saldo suficiente y dentro del límite autónomo.* |
| **3** | Intento de Cobro Duplicado | Telegram | `Factura_AWS_Cloud.pdf` (Reenvío) | $1,200,000 COP | **$285.71 USD** | 🔴 `REJECTED` | `INTEG-01` | *Cobro duplicado detectado dentro de la ventana de 30 días.* |
| **4** | Licencia de Software Mayor | Telegram | `Factura_Oracle_EUR.pdf` | €3,200 EUR | **$3,478.26 USD** | 🟠 `SCALED_TO_HUMAN` | `HITL-01` | *Excede el límite autónomo de $2,000 USD. Requiere aprobación humana.* |

---

## 🛠️ 5. Instrucciones para Actualizar el Repositorio

Para publicar este documento en la carpeta `docs/` de tu proyecto, puedes ejecutar los siguientes comandos en tu terminal local:

```bash
# Copiar la nueva versión al repositorio
cp presentacion_y_guion_v3.md docs/presentacion_y_guion_v3.md

# Confirmar cambios en git
git add docs/presentacion_y_guion_v3.md
git commit -m "docs: agregar V3 de la presentacion y guion con el escenario del lector biometrico"
git push origin main
```
