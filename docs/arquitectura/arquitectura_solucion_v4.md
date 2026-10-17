# Especificación de Arquitectura v4: Blinka PayAgent (Paybot)
**Proyecto:** Agentes Autónomos para Pagos Corporativos | **Hackathon 30X**
**Despliegue:** Railway All-in-One PaaS | **Repositorio:** `Oriojas/30X_404_team`

---

## 1. Visión General de la Arquitectura

Siguiendo el consenso técnico entre **Oscar Riojas** y **Luis Felipe Marín Giraldo**, la arquitectura de **Blinka PayAgent** adopta un patrón **Hexagonal (Puertos y Adaptadores)** dentro de un **Monorepo** en GitHub.

Esta arquitectura separa completamente los adaptadores de entrada (Telegram, API REST) y los adaptadores de salida (Gemini, tasas FX, PostgreSQL, notificaciones de Telegram) del **Núcleo de Negocio (Core)**, garantizando que nuevas fuentes de ingesta (como correo electrónico o WhatsApp) se puedan conectar sin modificar las reglas de procesamiento.

```mermaid
flowchart TD
    subgraph System ["ARQUITECTURA HEXAGONAL: BLINKA PAYAGENT"]
        direction TB

        subgraph InAdapters ["ADAPTADORES DE ENTRADA (adapters/inbound)"]
            Telegram["Telegram Webhook (MVP) - Ingesta Fotos/PDF y Botones HITL"]
            RestAPI["API REST FastAPI - /api/invoices y /api/rules"]
            OtherChannels["Canales Secundarios (Ext) - WhatsApp y Email Webhooks"]
        end

        subgraph Core ["CORE DEL SISTEMA (core/ - Logica de Negocio Pura)"]
            UseCases["Casos de Uso - ProcessInvoice, ListInvoices, Get/UpdateRules"]
            FX["FX Engine (Conversion a USD a $0 Markup)"]
            Rules["Motor de Reglas Blinka (Tuberia de Decision en 4 Capas)"]
            Audit["Generador de Explicabilidad (Audit Log Estructurado)"]
            Ports["Puertos de Salida - OCRPort, FXRateProvider, InvoiceRepository, RulesRepository, NotificationPort"]

            UseCases --> FX --> Rules --> Audit
            UseCases --> Ports
        end

        subgraph OutAdapters ["ADAPTADORES DE SALIDA (adapters/outbound)"]
            Gemini["Gemini 1.5 Flash - OCR Multimodal"]
            Rates["Proveedor de Tasas FX"]
            DB[("PostgreSQL (Railway Native) - invoices, company_rules")]
            TgClient["Cliente API Telegram - Notificaciones HITL"]
        end

        ReactUI["React.js y Tailwind UI - Landing Comercial y Dashboard Stitch"]

        ReactUI -->|"HTTP"| RestAPI
        Telegram -->|"Documento (PDF/Foto)"| UseCases
        RestAPI --> UseCases
        OtherChannels -.->|"Documento"| UseCases
        Ports -.->|"implementa"| Gemini
        Ports -.->|"implementa"| Rates
        Ports -.->|"implementa"| DB
        Ports -.->|"implementa"| TgClient
    end

    style System fill:#f8fafc,stroke:#475569,stroke-width:2px
    style InAdapters fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style OutAdapters fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    style Core fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ReactUI fill:#fefce8,stroke:#ca8a04,stroke-width:2px
```

**Regla de dependencias:** los adaptadores dependen del Core, nunca al revés. El Core solo conoce los puertos; el *composition root* (`backend/app/container.py`) decide qué adaptador concreto implementa cada puerto.

---

## 2. Estructura del Monorepo (`Oriojas/30X_404_team`)

```text
30X_404_team/
├── backend/                        # API FastAPI & Core Hexagonal
│   ├── app/
│   │   ├── core/                   # Hexágono: lógica de negocio pura
│   │   │   ├── domain/             # models.py, fx_converter.py, rules_pipeline.py, audit_logger.py
│   │   │   ├── ports/              # outbound.py: contratos que implementan los adaptadores
│   │   │   └── use_cases/          # process_invoice.py, query_invoices.py, manage_rules.py
│   │   ├── adapters/
│   │   │   ├── inbound/            # Adaptadores de entrada
│   │   │   │   ├── api/            # Routers REST, DTOs Pydantic, dependencias
│   │   │   │   └── telegram/       # Webhook de Telegram
│   │   │   └── outbound/           # Adaptadores de salida
│   │   │       ├── ocr/            # Gemini 1.5 Flash
│   │   │       ├── fx/             # Proveedor de tasas de cambio
│   │   │       ├── db/             # PostgreSQL + schema.sql
│   │   │       └── telegram/       # Cliente API Telegram (notificaciones HITL)
│   │   ├── config.py               # Settings desde el .env raíz
│   │   ├── container.py            # Composition root (inyección de dependencias)
│   │   └── main.py                 # Arranque FastAPI y montaje de routers
│   ├── tests/                      # Pruebas del Core con adaptadores falsos
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                       # Aplicación React + Tailwind CSS
│   ├── src/
│   │   ├── components/             # Dashboard, Audit Table, Rule Controls
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docs/                           # Documentación & Especificaciones
│   ├── arquitectura/arquitectura_solucion_v4.md
│   └── reglas-negocio/reglas_pago_agente_v3.md
├── plan_de_trabajo.md
└── README.md                       # Presentación del proyecto y guías
```

---

## 3. Tubería de Reglas de Negocio & FX Engine

```mermaid
flowchart TD
    Doc["Factura o Cuenta de Cobro (PDF/Imagen)"] --> OCR["Extraccion Multimodal (Gemini 1.5 Flash) - Monto, Moneda, Proveedor, Cuenta"]

    subgraph Pipeline ["Tuberia Determinista en 4 Capas"]
        Capa1["Capa 1: Compliance y SARLAFT (Listas OFAC/ONU y Cuentas Autorizadas)"]
        Capa2["Capa 2: Integridad y Duplicados (Chequeo 30 dias y Confianza OCR > 85%)"]
        Capa3["Capa 3: Solvencia y FX Engine (Normalizacion USD a $0 Markup y Saldo Blinka)"]
        Capa4["Capa 4: Gobierno y Human-in-the-Loop (Umbral $2,000 USD y Proveedor Nuevo)"]

        Capa1 -->|"Pasa"| Capa2
        Capa2 -->|"Pasa"| Capa3
        Capa3 -->|"Pasa"| Capa4
    end

    OCR --> Capa1

    Capa1 -->|"Alerta Critica"| Rejected["REJECTED - Rechazo Automatico"]
    Capa2 -->|"Duplicado"| Rejected
    Capa3 -->|"Saldo Insuficiente"| Scaled["SCALED_TO_HUMAN - Escalamiento con Boton Telegram"]
    Capa4 -->|"Excede Umbral"| Scaled
    Capa4 -->|"100% Criterios Cumplidos"| Approved["AUTO_APPROVED - Aprobado Autonomamente"]

    style Doc fill:#f8fafc,stroke:#64748b,stroke-width:2px
    style OCR fill:#fdf4ff,stroke:#c026d3,stroke-width:2px
    style Pipeline fill:#f1f5f9,stroke:#475569,stroke-width:1px
    style Capa1 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa2 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa3 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Capa4 fill:#eff6ff,stroke:#3b82f6,stroke-width:1px
    style Approved fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style Scaled fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style Rejected fill:#fee2e2,stroke:#dc2626,stroke-width:2px
```

### Capa 1: Compliance & SARLAFT
- Cotejo automático contra listas restrictivas (OFAC, ONU, listas locales).
- Validación de que la cuenta bancaria de destino pertenezca al beneficiario registrado.

### Capa 2: Integridad & Detección de Duplicados
- Detección de facturas duplicadas en un periodo de 30 días (`vendor_id` + `invoice_number`).
- Calidad mínima de lectura OCR (>85% de confianza).

### Capa 3: Solvencia & Conversión de Divisas (FX Engine)
- **Extracción de Moneda:** Soporte para facturas en COP, MXN, EUR, BRL, ARS y USD.
- **Normalización FX:** Conversión automática a USD usando la tasa de cambio de referencia.
- **Garantía Blinka:** Transacciones con **$0.00 FX Markup**.
- **Presupuesto:** Verificación de saldo disponible en la cuenta USD de Blinka (`balance_usd >= usd_amount`).

### Capa 4: Gobierno & Human-in-the-Loop (HITL)
- **Límite Autónomo:** Aprobación automática hasta **$2,000 USD** equivalente.
- **Escalamiento:** Si la factura supera $2,000 USD o es un proveedor nuevo, el bot de Telegram envía un mensaje interactivo con botones (*Inline Keyboard*) para aprobación humana en 1 clic.

---

## 4. Esquema de Base de Datos PostgreSQL

```sql
CREATE TABLE company_rules (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    max_autonomous_usd NUMERIC(12,2) DEFAULT 2000.00,
    sarlaft_check_enabled BOOLEAN DEFAULT TRUE,
    duplicate_check_days INT DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_name VARCHAR(150) NOT NULL,
    vendor_tax_id VARCHAR(50),
    original_amount NUMERIC(14,2) NOT NULL,
    original_currency VARCHAR(10) NOT NULL,
    fx_rate_applied NUMERIC(10,4),
    usd_amount NUMERIC(12,2) NOT NULL,
    due_date DATE,
    channel_source VARCHAR(30) DEFAULT 'TELEGRAM',
    decision_status VARCHAR(30) NOT NULL, -- AUTO_APPROVED, SCALED_TO_HUMAN, REJECTED
    audit_explanation TEXT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Despliegue en Railway (All-in-One PaaS)

El proyecto se despliega dentro de un único canvas de Railway:
1. **PostgreSQL Service:** Base de datos relacional administrada.
2. **Backend Service:** FastAPI container ejecutando el webhook de Telegram y la lógica de Gemini.
3. **Frontend Service:** React.js compilado servido con URL pública HTTPS.
4. **Environment Variables:** `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`.
