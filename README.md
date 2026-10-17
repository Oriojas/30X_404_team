# Blinka PayAgent (Paybot)

> **Agente Inteligente de Gestión y Control Autónomo de Pagos Corporativos**  
> *Proyecto desarrollado para la **Hackathon 30X** por el **Equipo 404** en el Reto **Blinka**.*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![Google Gemini](https://img.shields.io/badge/Gemini_3.8_Flash-4285F4?style=flat&logo=google)](https://ai.google.dev)
[![Railway](https://img.shields.io/badge/Railway-All--in--One-0B0D0E?style=flat&logo=railway)](https://railway.app)

---

## 📌 Resumen Ejecutivo

**Blinka PayAgent** automatiza el ciclo de vida de recepción, validación, conversión cambiaria y auditoría de facturas y cuentas de cobro para empresas globales con operaciones en Latinoamérica:

* 🤖 **Ingesta Multicanal:** Recepción inmediata de documentos contables (imágenes y PDFs) a través de un bot de Telegram o de la subida de archivos en el dashboard. Los canales solo ingresan facturas; las aprobaciones se hacen en el dashboard.
* 👁️ **Visión Multimodal (Gemini 3.8 Flash):** Extracción estructurada y normalización de montos, proveedores, fechas e ítems.
* 💱 **FX Engine ($0.00 FX Markup):** Conversión automática a USD en tiempo real para monedas locales (COP, MXN, EUR, BRL) sin sobrecostos cambiarios, apalancando las ventajas de las cuentas Blinka.
* 🛡️ **Tubería Determinista en 4 Capas:**
  1. *Cumplimiento & SARLAFT:* Bloqueo de proveedores en listas restrictivas o sin verificación fiscal.
  2. *Integridad Contable:* Detección infalible de facturas duplicadas en ventana de 30 días.
  3. *Solvencia Corporativa:* Verificación de fondos en USD y cupo mensual disponible.
  4. *Gobierno HITL (Human-in-the-Loop):* Aprobación 100% autónoma hasta **$2,000 USD**; operaciones mayores, proveedores nuevos o alertas de cumplimiento se escalan al **dashboard** para aprobación humana.
* 📜 **Audit Log Explicable:** Trazabilidad completa con registro en lenguaje natural para el equipo financiero.

---

## 🏛️ Estructura del Monorepo y Documentación Modular

El repositorio está organizado como un **Monorepo Hexagonal** centralizado. Para consultar la documentación detallada de cada módulo, accede a los siguientes enlaces:

* ⚙️ **[Backend (FastAPI & Arquitectura Hexagonal)](backend/README.md):** Arquitectura de puertos y adaptadores, conectores de Telegram y PostgreSQL, pipeline de reglas y endpoints REST.
* 🎨 **[Frontend (React, Vite & Tailwind CSS)](frontend/README.md):** Dashboard del equipo financiero, métricas de gobernanza, controles de umbral en tiempo real y tabla de auditoría.
* 🧭 **[Constitución del Proyecto](specs/):** [Misión](specs/mission.md), [Stack Tecnológico](specs/tech-stack.md) y [Roadmap](specs/roadmap.md) por fases pequeñas.
* 📋 **[Plan de Trabajo Oficial](plan_de_trabajo.md):** Fases de ejecución, cronograma, entregables y asignación de responsabilidades.
* 📐 **[Arquitectura de Solución v5](docs/arquitectura/arquitectura_solucion_v5.md):** Diagramas C4 (contexto, contenedores, componentes), flujos end-to-end, modelo de datos y despliegue.
* 📖 **[Reglas de Negocio del Agente](docs/reglas-negocio/reglas_pago_agente_v3.md):** Definición detallada de las 4 capas de validación y casos de uso.
* 📊 **[Presentación Comercial y Guion (Pitch)](docs/pitch_presentacion/presentacion_y_guion.md):** Estructura del slide deck y guion cronometrado de 3 minutos.

---

## 🔒 Reglas Estrictas de Configuración del Monorepo

Para garantizar reproducibilidad y evitar dispersión de configuraciones:

1. **Un solo archivo `.env` en la raíz:**
   - Todas las variables de entorno de la solución (Backend, Frontend, PostgreSQL, Telegram y Gemini) se declaran exclusivamente en el archivo raíz `.env`.
   - Se provee una plantilla única y completa en [.env.example](.env.example) con valores genéricos y documentados. No se permiten archivos `.env` secundarios en subdirectorios.
2. **Un solo archivo `.gitignore` en la raíz:**
   - Un único [.gitignore](.gitignore) centralizado administra las exclusiones de código compilado de Python, dependencias de Node.js, variables privadas y artefactos de despliegue.

---

## 🚀 Guía de Inicio Rápido

### 1. Clonar el repositorio y configurar variables de entorno
```bash
git clone https://github.com/Oriojas/30X_404_team.git
cd 30X_404_team
cp .env.example .env
# Edita .env con tus claves de Gemini, Telegram y PostgreSQL
```

### 2. Iniciar el Backend (FastAPI)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Swagger UI disponible en `http://localhost:8000/docs`.

### 3. Iniciar el Frontend (React + Vite)
En una nueva terminal:
```bash
cd frontend
npm install
npm run dev
```
Dashboard disponible en `http://localhost:3000`.

---

## ☁️ Despliegue en Railway (All-in-One)

El proyecto está preparado para desplegarse dentro de un único Canvas en **Railway**:
1. **PostgreSQL Native Service:** Base de datos relacional administrada. El backend aplica [schema.sql](backend/app/adapters/outbound/db/schema.sql) al arrancar (`DB_AUTO_MIGRATE=true`). Para la demo, activa `DB_SEED_DEMO=true` para cargar los datos ficticios de [seed.sql](backend/app/adapters/outbound/db/seed.sql).
2. **Backend Service:** Construido a partir de [backend/Dockerfile](backend/Dockerfile).
3. **Frontend Service:** Construido a partir de [frontend/Dockerfile](frontend/Dockerfile) y servido con Nginx.

* 🌐 **Landing Page & Dashboard:** [https://30x404team-production.up.railway.app](https://30x404team-production.up.railway.app/)
* 📽️ **Presentación en Vivo (Slide Deck):** [https://30x404team-production.up.railway.app/#/pitch/1](https://30x404team-production.up.railway.app/#/pitch/1)

---

## 👥 Equipo 404 (Hackathon 30X)

* **Luis Felipe Marín Giraldo** — Lead Backend & Bot Developer (FastAPI, Telegram Webhook, Gemini OCR, FX Engine & PostgreSQL).
* **Oscar Riojas** — Lead Frontend, Product & Pitch (Monorepo, Arquitectura, React Dashboard, Tailwind UI, Pitch & Video).

---

### 🎯 Presentación Comercial & Pitch
Accede a la presentación interactiva directamente en producción:  
👉 **[Ver Presentación (Slide Deck)](https://30x404team-production.up.railway.app/#/pitch/1)**  
📄 Documentación y guion: [docs/pitch_presentacion/presentacion_y_guion.md](docs/pitch_presentacion/presentacion_y_guion.md)