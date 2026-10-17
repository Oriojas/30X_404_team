# Índice de Documentación: Blinka PayAgent (Hackathon 30X)

Bienvenido a la documentación oficial y técnica del proyecto **Blinka PayAgent**, desarrollado por el equipo `30X_404_team` para la **Hackathon 30X**.

Este directorio centraliza la arquitectura, especificaciones funcionales, reglas de negocio y tokens de diseño del agente.

---

## Estructura del Directorio

```text
docs/
├── README.md                          # Este índice de navegación
├── arquitectura/                      # Arquitectura de sistemas y despliegue
│   ├── arquitectura_solucion_v5.md    # [VIGENTE] Arquitectura C4 (Contexto, Contenedores, Componentes, Código) tal como está implementada
│   ├── arquitectura_solucion_v4.md    # [Histórico] Arquitectura Hexagonal Monorepo (Puertos y Adaptadores + FX Engine)
│   ├── arquitectura_solucion_v3.md    # [Histórico] Arquitectura Gemini All-in-One
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

> **Nota:** El [Plan de Trabajo Oficial (plan_de_trabajo.md)](../plan_de_trabajo.md) se encuentra disponible en la raíz del repositorio con el cronograma por fases y la división de roles del equipo.

---

## 📌 Documentos Vigentes y de Referencia Principal

Para evaluar la solución durante la Hackathon, los documentos oficiales de referencia son:

1. **[Arquitectura de Solución (v5)](arquitectura/arquitectura_solucion_v5.md):**  
   Arquitectura **tal como está implementada**, con el modelo **C4**: contexto, contenedores, componentes del hexágono (puertos, casos de uso y adaptadores), flujos de una factura y de la decisión humana, modelo de datos, despliegue en Railway y decisiones de arquitectura.

2. **[Plan de Trabajo Oficial](../plan_de_trabajo.md):**  
   Cronograma por fases (Viernes 16 a Domingo 18), asignación de roles entre Oscar Riojas y Luis Felipe Marín Giraldo, y suite de casos de prueba.

3. **[Reglas de Negocio y Pipeline Determinista (v3)](reglas-negocio/reglas_pago_agente_v3.md):**  
   Especificación detallada de las 4 capas de evaluación (Compliance/SARLAFT, Integridad, Solvencia y Gobernanza HITL), matriz de reglas (COMP, INTEG, FIN, HITL), test suite obligatorio y formato del Audit Log.

4. **[Especificación Funcional de la Solución](especificaciones/especificacion_solucion.md):**  
   Flujo conversacional de ingesta vía Telegram, extracción multimodal y experiencia del dashboard administrativo.

5. **[Sistema de Diseño y Tokens](diseno/DESIGN.md):**  
   Paleta de colores oficial de Blinka (`#04243C`, `#2B9CAE`, `#1D3557`), tipografías, componentes y lineamientos de interfaz.

---

## 🕒 Histórico de Versiones

Las carpetas `arquitectura/` y `reglas-negocio/` conservan las versiones anteriores (`v1` a `v4` y `v1` a `v2`, respectivamente) como registro de la evolución del diseño técnico y conceptual del proyecto durante el desarrollo.
