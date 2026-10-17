# Blinka PayAgent — Frontend Dashboard

Interfaz web moderna y reactiva desarrollada con **React 18**, **Vite** y **Tailwind CSS**, inspirada en los lineamientos visuales oficiales de **Blinka** (azul marino corporativo `#04243C`, cian de acento `#2B9CAE` y azul marino profundo `#1D3557`).

Permite al equipo financiero visualizar métricas en tiempo real, auditar la trazabilidad de cada decisión autónoma y ajustar parámetros de gobernanza en 1 clic.

---

## 🧩 Componentes Principales

```text
frontend/src/
├── components/
│   ├── Navbar.jsx             # Barra superior con insignia de salud y conexión Railway
│   ├── DashboardMetrics.jsx   # 4 KPIs principales (Total, Auto-Aprobadas, Escaladas HITL, Rechazadas)
│   ├── AuditTable.jsx         # Tabla del Audit Log con badges de estado y explicabilidad en lenguaje natural
│   └── RuleControls.jsx       # Panel interactivo de ajuste de umbrales y políticas de pago
├── App.jsx                    # Contenedor central con estado reactivo y llamadas REST a FastAPI
├── index.css                  # Directivas de Tailwind CSS y tipografía Inter
└── main.jsx                   # Punto de entrada de React en el DOM
```

---

## ⚙️ Variables de Entorno

> [!IMPORTANT]
> Siguiendo las reglas del monorepo, **la configuración se define exclusivamente en el archivo `.env` del directorio raíz**. No se utilizan archivos `.env` locales en `frontend/`.

* `VITE_API_BASE_URL`: URL base del backend FastAPI (ej: `http://localhost:8000` en local o la URL generada en Railway).

Consulta la plantilla completa en [.env.example](../.env.example).

---

## 🚀 Ejecución Local

### 1. Instalar dependencias
Desde la carpeta `frontend/`:
```bash
cd frontend
npm install
```

### 2. Iniciar el servidor de desarrollo
```bash
npm run dev
```
La aplicación iniciará en `http://localhost:3000` con Hot Module Replacement (HMR).

### 3. Construir para producción
```bash
npm run build
```
Genera los archivos estáticos optimizados en `frontend/dist/`.

---

## 🐳 Despliegue con Docker y Nginx (Railway)

El archivo [Dockerfile](Dockerfile) utiliza un esquema *multi-stage build*:
1. **Builder:** Compila el frontend con Node.js 20.
2. **Runner:** Sirve los archivos estáticos mediante Nginx Alpine.

Usa [nginx.conf.template](nginx.conf.template), la cual sustituye automáticamente la variable `$PORT` inyectada por Railway al iniciar el contenedor.

```bash
docker build -t blinka-frontend -f frontend/Dockerfile frontend/
docker run -p 80:80 -e PORT=80 blinka-frontend
```

---

## 🎨 Paleta de Diseño Oficial Blinka

* **Fondo Principal:** `#F8FAFC` (Slate 50)
* **Azul Marino Corporativo:** `#04243C` (Header, tarjetas de héroe y botones primarios)
* **Cian Blinka (Acento):** `#2B9CAE` (Insignias, bordes activos y $0.00 FX Markup)
* **Azul Noche Profundo:** `#1D3557` (Gradientes y estados hover)
* **Estados de Auditoría:**
  - `AUTO_APPROVED`: Verde Esmeralda (`bg-emerald-100 text-emerald-800`)
  - `SCALED_TO_HUMAN`: Ámbar Cálido (`bg-amber-100 text-amber-800`)
  - `REJECTED`: Rosa / Rojo Coral (`bg-rose-100 text-rose-800`)

---

## 🔗 Referencias
* [README Principal del Proyecto](../README.md)
* [Backend (FastAPI Hexagonal)](../backend/README.md)
* [Especificación de Diseño](../docs/diseno/DESIGN.md)
