# Blinka PayAgent — Frontend Dashboard

Interfaz web moderna y reactiva desarrollada con **React 18**, **Vite** y **Tailwind CSS**, inspirada en los lineamientos visuales oficiales de **Blinka** (azul marino corporativo `#04243C`, cian de acento `#2B9CAE` y azul marino profundo `#1D3557`).

Permite al equipo financiero subir facturas, auditar la trazabilidad de cada decisión capa por capa, aprobar o rechazar los escalamientos (la aprobación humana ocurre solo aquí) y ajustar las reglas de gobernanza.

---

## 🧩 Componentes Principales

```text
frontend/src/
├── api.js                     # Cliente REST: único punto que llama a la API (fetch, errores, Idempotency-Key)
├── status.js                  # Mapa único de estados (etiquetas, colores) y métrica de autonomía
├── components/
│   ├── Navbar.jsx             # Barra superior
│   ├── RuleControls.jsx       # Reglas de gobernanza: carga y guarda en /api/rules, errores 422 por campo
│   ├── AuditTable.jsx         # Audit Log: métricas, subida, filtros por estado, botón Actualizar y modo demostración
│   ├── DashboardMetrics.jsx   # KPIs: total, autonomía, pendientes HITL y decisiones humanas
│   ├── InvoiceUpload.jsx      # Subida de facturas con Idempotency-Key y reintentos
│   ├── AuditDrawer.jsx        # Inspector de decisión: evaluación capa por capa y decisión humana
│   └── StatusBadge.jsx        # Badge de estado compartido
├── App.jsx                    # Estado central: facturas, reglas, modo demostración
├── index.css                  # Directivas de Tailwind CSS y tipografía Inter
└── main.jsx                   # Punto de entrada de React en el DOM
```

---

## ⚙️ Variables de Entorno

> [!IMPORTANT]
> Siguiendo las reglas del monorepo, **la configuración se define exclusivamente en el archivo `.env` del directorio raíz**. No se utilizan archivos `.env` locales en `frontend/`.

* `VITE_API_BASE_URL`: URL base del backend FastAPI (ej: `http://localhost:8000` en local o la URL generada en Railway). Vite la lee del `.env` de la raíz (`envDir: '..'` en [vite.config.js](vite.config.js)). El backend debe incluir el origen del frontend en `ALLOWED_ORIGINS`.

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

## 🔌 Integración con la API

* **Audit Log:** se carga de `GET /api/invoices` al abrir la página y con el botón **Actualizar** (sin actualización automática). Si la API responde, se muestran siempre los datos reales, aunque la lista esté vacía.
* **Modo demostración:** si la API no responde (o falta `VITE_API_BASE_URL`), se muestran datos ficticios con un aviso visible y se deshabilitan la subida, la decisión humana y el guardado de reglas.
* **Evaluación capa por capa:** el Drawer muestra `evaluations` en el orden de la tubería (Compliance, Integridad, Solvencia, Gobierno HITL) con su estado, las alertas (código + explicación) y la razón de las capas omitidas.
* **Decisión humana:** solo en el dashboard. `POST /api/invoices/{id}/decision` con `decided_by` fijo (`CFO Demo`, sin autenticación en el MVP) y una nota opcional. Un `409` (otra persona ya decidió) muestra el mensaje y recarga el estado vigente.
* **Subida de facturas:** JPG, PNG, WEBP o PDF de hasta 10 MB (validado también en el navegador). Cada archivo elegido genera una `Idempotency-Key` (`crypto.randomUUID()`) que se reutiliza en los reintentos: `201` y `200` muestran la factura igual, y un `409` (aún en proceso) se reintenta hasta 3 veces cada 2 s.
* **Reglas:** `POST /api/rules`; el panel solo cambia con la respuesta de la API y muestra los errores `422` junto a cada campo.
* **Autonomía:** `(AUTO_APPROVED + REJECTED) / total`; las decisiones `HUMAN_*` no cuentan como autónomas.

---

## 🐳 Despliegue con Docker y Nginx (Railway)

El archivo [Dockerfile](Dockerfile) utiliza un esquema *multi-stage build*:
1. **Builder:** Compila el frontend con Node.js 20.
2. **Runner:** Sirve los archivos estáticos mediante Nginx Alpine.

Nginx ([nginx.conf.template](nginx.conf.template)) solo sirve el build estático en el `$PORT` que inyecta Railway. **No hay proxy `/api/`**: el dashboard llama al backend por su URL pública (`VITE_API_BASE_URL`) y el backend lo autoriza con CORS (`ALLOWED_ORIGINS`).

`VITE_API_BASE_URL` se incrusta en el JavaScript **durante el build**. El Dockerfile la declara como `ARG`, que es la forma en que Railway la recibe. Si cambia, hay que volver a construir la imagen (redeploy). Una imagen construida sin ella queda en modo demostración.

```bash
docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t blinka-frontend frontend/
docker run -p 8080:8080 -e PORT=8080 blinka-frontend
```

En Railway el servicio `30X_404_team` está declarado en [.railway/railway.ts](../.railway/railway.ts), con `VITE_API_BASE_URL` apuntando al dominio del `backend`. Los pasos de despliegue están en [backend/README.md](../backend/README.md#️-despliegue-en-railway).

---

## 🎨 Paleta de Diseño Oficial Blinka

* **Fondo Principal:** `#F8FAFC` (Slate 50)
* **Azul Marino Corporativo:** `#04243C` (Header, tarjetas de héroe y botones primarios)
* **Cian Blinka (Acento):** `#2B9CAE` (Insignias, bordes activos y elementos destacados)
* **Azul Noche Profundo:** `#1D3557` (Gradientes y estados hover)
* **Estados de Auditoría:**
  - `AUTO_APPROVED`: Verde Esmeralda (`bg-emerald-100 text-emerald-800`)
  - `SCALED_TO_HUMAN`: Ámbar Cálido (`bg-amber-100 text-amber-800`)
  - `REJECTED`: Rojo Coral (`bg-red-50 text-red-800`)
  - `HUMAN_APPROVED` / `HUMAN_REJECTED`: mismos tonos que aprobado / rechazado, con ícono de persona
  - Definidos una sola vez en [src/status.js](src/status.js)

---

## 🔗 Referencias
* [README Principal del Proyecto](../README.md)
* [Backend (FastAPI Hexagonal)](../backend/README.md)
* [Especificación de Diseño](../docs/diseno/DESIGN.md)
