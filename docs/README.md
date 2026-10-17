# Índice de Documentación: Blinka PayAgent (Hackathon 30X)

Bienvenido a la documentación oficial y técnica del proyecto **Blinka PayAgent**, desarrollado por el equipo `30X_404_team` para la **Hackathon 30X**.

Este directorio centraliza la arquitectura, especificaciones funcionales, reglas de negocio y tokens de diseño del agente.

---

## Estructura del Directorio

```text
docs/
├── README.md                          # Este índice de navegación
├── arquitectura/                      # Arquitectura de sistemas y despliegue
│   ├── arquitectura_solucion_v3.md    # [VIGENTE] Arquitectura Gemini All-in-One (FastAPI + React + Postgres + Gemini)
│   ├── arquitectura_solucion_v2.md    # [Histórico] Arquitectura híbrida (Gemini Flash + DeepSeek)
│   └── arquitectura_solucion_v1.md    # [Histórico] Versión inicial de arquitectura
├── reglas-negocio/                    # Políticas, pipeline determinista y compliance
│   ├── reglas_pago_agente_v3.md       # [VIGENTE] Matriz completa, pipeline en 4 capas y test suite
│   ├── reglas_pago_agente_v2.md       # [Histórico] Segunda iteración de reglas y alcance
│   └── reglas_pago_agente_v1.md       # [Histórico] Borrador inicial de políticas
├── especificaciones/                 # Visión de la solución y casos de uso
│   └── especificacion_solucion.md     # Flujo funcional Telegram + OCR + Landing/Dashboard
└── diseno/                            # Identidad visual y tokens UI
    └── DESIGN.md                      # Design System, tokens de color (Blinka) y tipografía
```

---

## 📌 Documentos Vigentes y de Referencia Principal

Para evaluar la solución durante la Hackathon, los documentos oficiales de referencia son:

1. **[Arquitectura de Solución (v3)](arquitectura/arquitectura_solucion_v3.md):**  
   Define el stack unificado alrededor de **Google Gemini** (OCR multimodal + motor de razonamiento de reglas), servidor FastAPI en Python, PostgreSQL nativo en Railway y frontend en React.js con Tailwind CSS.

2. **[Reglas de Negocio y Pipeline Determinista (v3)](reglas-negocio/reglas_pago_agente_v3.md):**  
   Especificación detallada de las 4 capas de evaluación (Compliance/SARLAFT, Integridad, Solvencia y Gobernanza HITL), matriz de reglas (COMP, INTEG, FIN, HITL), test suite obligatorio y formato del Audit Log.

3. **[Especificación Funcional de la Solución](especificaciones/especificacion_solucion.md):**  
   Flujo conversacional de ingesta vía Telegram, extracción multimodal y experiencia del dashboard administrativo.

4. **[Sistema de Diseño y Tokens](diseno/DESIGN.md):**  
   Paleta de colores oficial de Blinka (`#04243C`, `#2B9CAE`, `#1D3557`), tipografías, componentes y lineamientos de interfaz.

---

## 🕒 Histórico de Versiones

Las carpetas `arquitectura/` y `reglas-negocio/` conservan las versiones anteriores (`v1` y `v2`) como registro de la evolución del diseño técnico y conceptual del proyecto durante el desarrollo.
