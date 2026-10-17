# Plan de Trabajo Oficial: Blinka PayAgent (Paybot)
**Proyecto para Hackathon 30X | Equipo 404**
**Repositorio GitHub:** `Oriojas/30X_404_team`
**Fecha de Inicio:** 16 de Octubre de 2026 | **Fecha Límite de Entrega:** 18 de Octubre de 2026 - 11:59 AM (GMT-5)

---

## 1. Resumen Ejecutivo del Proyecto

**Blinka PayAgent (Paybot)** es un agente autónomo e inteligente de gestión y control de pagos corporativos diseñado para empresas globales que operan con equipos y proveedores en Latinoamérica. Permite recibir facturas y cuentas de cobro desde múltiples canales (iniciando con un bot interactivo de Telegram como MVP), extraer la información mediante visión multimodal (Gemini 1.5 Flash), evaluar el pago contra una tubería de reglas de negocio de 4 capas (incluyendo conversión de divisas en tiempo real), y registrar cada decisión en un panel de auditoría (*Audit Log*) completamente explicable.

---

## 2. Arquitectura Técnica Hexagonal y Componentes Unificados

Basado en los acuerdos de la reunión con **Luis Felipe Marín Giraldo**, la solución adopta una **Arquitectura Hexagonal (Puertos y Adaptadores)** dentro de un **Monorepo** centralizado y desplegado en **Railway (All-in-One)**.

```mermaid
flowchart TD
    subgraph System ["ARQUITECTURA HEXAGONAL DE BLINKA PAYAGENT"]
        direction TB

        subgraph InAdapters ["ADAPTADORES DE ENTRADA (Canales de Ingesta)"]
            Telegram["<b>Telegram Bot (MVP)</b><br/>• Ingesta de Fotos / PDF<br/>• Botones Interactivos HITL"]
            OtherChannels["<b>Canales Secundarios (Ext)</b><br/>• Email / Webhook"]
        end

        subgraph OutAdapters ["ADAPTADOR DE SALIDA (UI / Capa de Presentación)"]
            ReactUI["<b>React.js + Tailwind UI</b><br/>• Landing Page Comercial<br/>• Dashboard Stitch & Audit Log"]
        end

        subgraph Core ["CORE DEL SISTEMA (Lógica de Negocio Hexagonal)"]
            OCR["<b>1. Lector Multimodal & OCR</b><br/>Gemini 1.5 Flash API"]
            FX["<b>2. FX Engine</b><br/>Conversión Multidivisa USD/COP/MXN/EUR ($0 Markup)"]
            Rules["<b>3. Motor de Reglas Blinka</b><br/>Tubería Determinista en 4 Capas"]
            Audit["<b>4. Generador de Explicabilidad</b><br/>Registro Audit Log en lenguaje natural"]

            OCR --> FX --> Rules --> Audit
        end

        subgraph PersistAdapter ["ADAPTADOR DE PERSISTENCIA"]
            DB[("<b>Base de Datos PostgreSQL (Railway Native)</b><br/>• Tabla invoices<br/>• Tabla audit_logs<br/>• Tabla company_rules")]
        end

        Telegram -->|"Documento (PDF/Foto)"| OCR
        OtherChannels -.->|"Documento"| OCR
        Audit -->|"Persistir Decisión"| DB
        ReactUI -->|"Consultas REST API"| Core
        ReactUI -.->|"Lectura Audit Log"| DB
    end

    style System fill:#f8fafc,stroke:#475569,stroke-width:2px
    style InAdapters fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style OutAdapters fill:#fefce8,stroke:#ca8a04,stroke-width:2px
    style Core fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style PersistAdapter fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
```

---

## 3. Módulo Especial: Regla de Conversión de Divisas (FX Engine)

Uno de los requerimientos clave del Reto Blinka es la gestión de operaciones multidivisa (pagos a proveedores en Latinoamérica en monedas locales como COP, MXN, EUR, BRL o ARS desde una cuenta corporativa en USD).

### Flujo de Conversión de Divisas:
1. **Extracción Multimodal (Gemini 1.5 Flash):** El OCR identifica el monto original (`original_amount`) y la moneda original (`original_currency`, ej: $1,500,000 COP, €450 EUR, $12,000 MXN).
2. **Normalización a USD (FX Engine):**
   - El Core consulta/aplica la tasa de cambio vigente (`fx_rate`).
   - Calcula el valor equivalente en dólares (`usd_amount = original_amount / fx_rate`).
   - Aplica el **$0.00 FX Markup** garantizado por las tarjetas y cuentas corporativas de Blinka.
3. **Evaluación contra las Reglas en USD:**
   - **Umbral de Autonomía:** Se compara el `usd_amount` contra el límite máximo autónomo (ej: **$2,000 USD**).
   - **Verificación de Saldo Blinka:** Se valida que la cuenta USD posea suficiente saldo disponible (`balance_usd >= usd_amount`).
   - **Presupuesto Mensual:** Se verifica que no se exceda el cupo acumulado en USD del periodo.
4. **Registro Audit Log Explicable:** Cada factura registrada guarda en la base de datos:
   ```json
   {
     "original_amount": 1500000.00,
     "original_currency": "COP",
     "fx_rate_applied": 4200.00,
     "blinka_fx_markup": "0.00 USD",
     "converted_usd_amount": 357.14,
     "evaluation": "AUTO_APPROVED",
     "reason": "Monto de $357.14 USD ($1,500,000 COP a tasa 4,200 COP/USD) está dentro del límite autónomo ($2,000 USD) y el proveedor está verificado."
   }
   ```

---

## 4. División de Trabajo y Asignación de Responsabilidades

| Integrante | Rol Principal | Entregables Clave |
| :--- | :--- | :--- |
| **Luis Felipe Marín Giraldo** | **Lead Backend & Bot Developer** | • Estructura del backend en FastAPI bajo Arquitectura Hexagonal.<br>• Adaptador para Bot de Telegram con manejo de webhooks y descarga de adjuntos.<br>• Integración con SDK de Gemini 1.5 Flash para OCR y motor de razonamiento.<br>• Lógica de la tubería de 4 capas y FX Engine.<br>• Conexión y persistencia con PostgreSQL en Railway. |
| **Oscar Riojas** | **Lead Frontend, Product & Pitch** | • Documentación completa de arquitectura y Plan de Trabajo en el monorepo.<br>• Configuración del monorepo en GitHub (`Oriojas/30X_404_team`) y carpetas `/backend`, `/frontend`, `/docs`.<br>• Frontend en React + Tailwind CSS con el diseño Stitch para Dashboard móvil/desktop.<br>• Consumo de API REST para renderizar el Audit Log de facturas.<br>• Creación del guion comercial, edición del Video Pitch (3 min) y presentación para el Demo Day. |

---

## 5. Cronograma de Ejecución por Fases (Viernes 16 - Domingo 18)

```mermaid
gantt
    title Cronograma de Ejecución: Hackathon 30X (Equipo 404)
    dateFormat YYYY-MM-DD HH:mm
    axisFormat %a %H:%M

    section FASE 1: Setup
    Monorepo e Infraestructura Railway :done, f1, 2026-10-16 18:00, 2026-10-16 23:59
    Script DDL en PostgreSQL :active, f1_db, 2026-10-16 21:00, 2026-10-16 23:59

    section FASE 2: Backend & IA
    Telegram Webhook Adapter :f2_tg, 2026-10-17 08:00, 2026-10-17 11:00
    Gemini OCR & Multimodal :f2_ocr, 2026-10-17 09:30, 2026-10-17 12:30
    FX Engine & Reglas 4 Capas :f2_rules, 2026-10-17 11:00, 2026-10-17 14:00
    Endpoints REST FastAPI :f2_api, 2026-10-17 13:00, 2026-10-17 15:00

    section FASE 3: Frontend & E2E
    React Dashboard Stitch UI :f3_ui, 2026-10-17 14:00, 2026-10-17 18:00
    Audit Log Table & Badges :f3_audit, 2026-10-17 16:00, 2026-10-17 20:00
    Pruebas E2E (Casos Trampa) :f3_tests, 2026-10-17 19:00, 2026-10-17 23:00

    section FASE 4: Cierre & Pitch
    Congelamiento de Código :crit, f4_freeze, 2026-10-18 09:00, 2026-10-18 09:30
    Grabación Video Pitch (3 min) :crit, f4_pitch, 2026-10-18 09:30, 2026-10-18 11:00
    Entrega Final en HackRadar :crit, f4_sub, 2026-10-18 11:00, 2026-10-18 11:59
```

### 🔴 FASE 1: Setup e Infraestructura Monorepo (Viernes 16 - Noche)
- [x] **Monorepo:** Configurar estructura hexagonal en `Oriojas/30X_404_team`.
- [x] **Railway Setup:** Proyecto `Blinka-PayAgent` en Railway con PostgreSQL, Backend FastAPI y Frontend React.
- [x] **Git Access:** Compartir acceso de GitHub a Luis Felipe Marín Giraldo y establecer ramas `main` y `develop`.
- [ ] **Base de Datos:** Ejecutar script DDL inicial en PostgreSQL (`invoices`, `audit_logs`).

### 🟡 FASE 2: Backend, OCR & Reglas de Negocio (Sábado 17 - Mañana)
- [ ] **Telegram Adapter:** Servidor FastAPI recibiendo Webhooks y fotos/PDFs de Telegram.
- [ ] **Gemini OCR Module:** Extracción estructurada JSON con Gemini 1.5 Flash.
- [ ] **FX Engine & Business Rules:** Lógica de conversión de monedas y evaluación de las 4 capas de negocio.
- [ ] **REST Endpoints:** Exposición de endpoints `/api/invoices` y `/api/rules` para el dashboard.

### 🟢 FASE 3: Frontend React, Dashboard & Pruebas E2E (Sábado 17 - Tarde / Noche)
- [ ] **React Dashboard:** Implementación del diseño Stitch con paleta de colores Blinka.
- [ ] **Audit Log Table:** Tabla interactiva mostrando insignias de estado y explicaciones en lenguaje natural.
- [ ] **Pruebas de Casos Normales y Casos Trampa:**
  1. Factura normal aprobada automáticamente.
  2. Factura duplicada (Frenada - `REJECTED`).
  3. Proveedor no verificado en SARLAFT (Frenada - `REJECTED`).
  4. Factura en divisas que supera límite $2,000 USD (Escalada a humano - `SCALED_TO_HUMAN`).
  5. Interacción interactiva desde Telegram con botones *Inline Keyboards* para aprobar escalamientos.

### 🔵 FASE 4: Cierre, Video Pitch & Entrega (Domingo 18 - Mañana)
- [ ] **Congelamiento de Código:** Cierre de commits a las 09:30 AM.
- [ ] **Video Pitch (3 Minutos):** Grabación enfocada en propuesta de valor comercial, demostración en vivo de Telegram + Dashboard, y ROI.
- [ ] **Publicación de Repositorio:** README final actualizado con documentación y link desplegado.
- [ ] **Entrega Final:** Subida en la plataforma HackRadar antes de las 11:59 AM.

---

## 6. Criterios de Éxito de la Solución (Alineación con Hackathon 30X)

1. **Autonomía (30% Impacto):** El agente procesa y decide el 100% de las facturas estándar sin intervención humana.
2. **Seguridad (Zero-Tolerance):** Cero pagos no autorizados. Detección infalible de duplicados, alertas SARLAFT y conversiones de moneda estrictas.
3. **Explicabilidad:** Registro claro en lenguaje natural para que el equipo financiero entienda la decisión de inmediato.
4. **Viabilidad de Implementación:** Despliegue en producción funcional en Railway con cero tiempo de caída (*Zero Downtime*).
