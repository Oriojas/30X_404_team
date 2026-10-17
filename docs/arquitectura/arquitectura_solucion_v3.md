# Arquitectura Tecnológica e Infraestructura: Blinka PayAgent (v3 - Gemini All-in-One)

## 1. Visión General y Definición del Stack

La solución **Blinka PayAgent** centraliza la lectura, validación y toma de decisiones sobre facturas corporativas en un stack unificado alrededor de **Google Gemini**, eliminando la dispersión de proveedores y maximizando la velocidad de ejecución para la Hackathon 30X.

```mermaid
flowchart TD
    subgraph Railway ["ARQUITECTURA DE INFRAESTRUCTURA EN RAILWAY"]
        Frontend["<b>FRONTEND (UI / Web)</b><br/>• React.js + Tailwind CSS<br/>• Dashboard & Audit Log<br/>• Landing Comercial"]
        Backend["<b>BACKEND (Python FastAPI)</b><br/>• Telegram Webhook Engine<br/>• Engine de Reglas Blinka<br/>• Gemini SDK Client"]
        Gemini["<b>GOOGLE GEMINI API</b><br/>• OCR & Extracción Multimodal<br/>• Razonamiento & Explicabilidad"]
        Database[("<b>BASE DE DATOS</b><br/>• PostgreSQL (Railway Native)<br/>• Tablas: invoices, audit_logs")]

        Frontend -->|"Consultas REST / API"| Backend
        Backend -->|"API Calls"| Gemini
        Backend -->|"Persistencia SQLAlchemy"| Database
        Gemini -.->|"JSON Estructurado & Explicación"| Backend
    end

    style Railway fill:#f8fafc,stroke:#64748b,stroke-width:2px
    style Frontend fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style Backend fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style Gemini fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style Database fill:#fefce8,stroke:#ca8a04,stroke-width:2px
```

---

## 2. Componentes del Stack Tecnológico

| Capa / Componente | Tecnología Seleccionada | Rol Específico en el Sistema |
| :--- | :--- | :--- |
| **Lector Multimodal & OCR** | **Gemini 1.5 Flash** | Procesa la foto o PDF recibido desde Telegram y extrae directamente el JSON estructurado (`vendor_name`, `tax_id`, `amount`, `currency`, `due_date`, `bank_details`). |
| **Motor de Razonamiento & Reglas** | **Gemini 1.5 Flash / Pro** | Evalúa las reglas de negocio en 4 capas de Blinka y redacta la explicación en lenguaje natural para el *Audit Log*. |
| **Canal de Ingesta Conversacional** | **Telegram Bot (Webhook)** | Recibe facturas por chat y notifica dictámenes o botones de aprobación rápida (*Human-in-the-Loop*). |
| **Backend & Servidor API** | **Python 3.12 + FastAPI** | Recibe webhooks, orquesta la llamada a Gemini, consulta PostgreSQL y expone la API REST para la interfaz web. |
| **Frontend & Dashboard** | **React.js + Tailwind CSS** | Presenta la landing page comercial y la consola de auditoría con la paleta de colores de Blinka (`#04243C`, `#2B9CAE`). |
| **Base de Datos & Persistencia** | **PostgreSQL (Railway)** | Almacena las facturas procesadas, la configuración de reglas y la trazabilidad de decisiones (*Audit Log*). |
| **Infraestructura All-in-One** | **Railway** | Aloja el Frontend, Backend y PostgreSQL en un solo lienzo visual con despliegue continuo desde GitHub. |

---

## 3. Análisis de Capacidad, Créditos y Viabilidad (Gemini PRO)

**Respuesta Directa:** **SÍ, TIENES MÁS QUE SUFICIENTES CRÉDITOS.**

### Plan Gratuito (Google AI Studio - Free Tier)
* **Límite:** 15 solicitudes por minuto (RPM) / 1,500 solicitudes por día (RPD).
* **Consumo Estimado para la Hackathon:** Procesar 100 facturas de prueba consume apenas el **6.6% del límite diario**.

### Plan Pro / Pay-as-you-go
* **Costo por Factura (Gemini 1.5 Flash):**
  * Entrada (Imagen + Prompt): ~2,000 tokens \\(\approx\\) \$0.00015 USD.
  * Salida (JSON Estructurado + Explicación): ~500 tokens \\(\approx\\) \$0.00015 USD.
  * **Costo Total por Factura:** **~\$0.0003 USD (Menos de un centavo de dólar por cada 30 facturas).**
* **Conclusión:** Tener tu cuenta PRO con un único proveedor (**Gemini API Key**) te brinda capacidad prácticamente ilimitada para todas las pruebas del fin de semana sin riesgo de agotamiento.

---

## 4. Ventajas de la Centralización en Gemini

1. **Una Sola API Key (`GEMINI_API_KEY`):** Simplifica la configuración de variables de entorno en Railway y entornos locales.
2. **Cero Fricción de Integración:** Un único SDK oficial (`google-generativeai`) instalado en `requirements.txt`.
3. **Flujo de Un Solo Paso (*One-Shot Processing*):** Gemini puede leer la imagen y evaluar las reglas en una sola llamada de API si se requiere máxima velocidad, o en dos pasos estructurados (OCR \\(\rightarrow\\) Reglas) para garantizar modularidad.

---

## 5. Tubería de Decisiones del Agente (4 Capas de Reglas)

```mermaid
flowchart TD
    In["Foto / PDF de Factura en Telegram"] --> Step1["<b>(1) OCR & Extracción en JSON</b><br/>(Gemini 1.5 Flash)"]

    subgraph Pipeline ["(2) Tubería de Reglas de Negocio (FastAPI / Gemini)"]
        L1["Capa 1: SARLAFT & Listas Restrictivas (OFAC/PEP)"]
        L2["Capa 2: Integridad & Detección de Duplicados (<30 días)"]
        L3["Capa 3: Solvencia & Saldo Disponible en Blinka"]
        L4["Capa 4: Gobierno HITL & Umbral Autónomo ($2,000 USD)"]

        L1 --> L2 --> L3 --> L4
    end

    Step1 --> L1
    L4 --> Step3["<b>(3) Generación de Dictamen & Explicación</b><br/>(Lenguaje Natural)"]

    Step3 --> Aprobado["<b>APROBADO</b><br/>(AUTO_APPROVED)"]
    Step3 --> Escalado["<b>ESCALADO</b><br/>(SCALED_TO_HUMAN)"]
    Step3 --> Rechazado["<b>RECHAZADO</b><br/>(REJECTED)"]

    Aprobado --> Step4["<b>(4) Persistencia y Notificación</b><br/>PostgreSQL + Telegram + Dashboard React"]
    Escalado --> Step4
    Rechazado --> Step4

    style In fill:#f8fafc,stroke:#64748b,stroke-width:2px
    style Step1 fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style Pipeline fill:#f8fafc,stroke:#475569,stroke-width:1px
    style Step3 fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style Aprobado fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style Escalado fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style Rechazado fill:#fee2e2,stroke:#dc2626,stroke-width:2px
    style Step4 fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
```

---

## 6. Entregables del Repositorio (`/docs`)

Este documento se encuentra guardado en tu repositorio bajo la ruta:
`docs/arquitectura/arquitectura_solucion_v3.md`
