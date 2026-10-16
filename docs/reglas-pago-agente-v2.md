# Especificación Técnica y Reglas de Negocio: Agente de Pagos Blinka (Hackathon 30X)

## 1. Visión General y Alcance del Reto

### El Problema
Las empresas constituidas en EE. UU. con equipos, proveedores y contratistas en Latinoamérica realizan decenas de pagos internacionales cada mes. El proceso actual involucra la recepción manual de facturas (PDF, correos, chats), verificación de tarifas, consulta de saldo, solicitud de aprobaciones por chat y carga manual en plataformas bancarias. Todo esto genera fricción, demoras y riesgo de errores de pago o fraudes.

### Delimitación del Alcance (Ficha Oficial de Blinka)

```
┌──────────────────────────────────────────────┬──────────────────────────────────────────────┐
│ ENTRA EN EL ALCANCE (Agente de Inteligencia) │ NO ENTRA EN EL ALCANCE (Fuera de Scope)      │
├──────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ ✓ Leer facturas/cuentas (PDF, imagen, texto) │ ✗ Ejecutar pagos reales o mover dinero real │
│   y extraer datos clave (quién, cuánto,      │ ✗ Abrir cuentas bancarias                    │
│   moneda, fecha límite).                     │ ✗ Proceso de KYB / Verificación de identidad │
│ ✓ Evaluar reglas de negocio configurables.   │   compleja de empresas                       │
│ ✓ Decidir: PAGAR, FRENAR o ESCALAR a humano. │ ✗ Motores complejos de fraude bancario       │
│ ✓ Generar Audit Log explicable por factura.  │ ✗ Rediseño de la app completa de Blinka      │
│ ✓ Dashboard interactivo de reglas e historial│                                              │
└──────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Criterios de Evaluación y Éxito de Blinka

Para maximizar el puntaje en la hackathon, la arquitectura del agente responde directamente a los 3 criterios oficiales de Blinka:

1. **Autonomía:** Porcentaje de facturas que el agente procesa correctamente sin requerir intervención humana.
2. **Seguridad (Tolerancia Cero):** Cero pagos aprobados fuera de las reglas establecidas. *Nota:* Aprobar un pago indebido descalifica automáticamente al proyecto.
3. **Explicabilidad:** Cualquier operador financiero puede entender por qué el agente **PAGÓ**, **FRENÓ** o **ESCALÓ** una factura leyendo su registro, sin inspeccionar código fuente.

---

## 3. Arquitectura de Decisiones en 4 Capas (Pipeline de Evaluación)

El agente procesa cada factura o cuenta de cobro de forma determinista mediante una tubería (*pipeline*) secuencial. Si falla una prueba crítica en las capas iniciales, la decisión se detiene de inmediato.

```
                  [ Factura / Cuenta de Cobro de Entrada ]
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: Compliance, SARLAFT & Seguridad                                   │
│ ¿Está en listas negras (OFAC/GAFI) o presenta cuenta no autorizada?      │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ No / Pasó
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: Integridad & Validación de Datos                                 │
│ ¿Es un cobro duplicado o excede la tarifa acordada?                      │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ No / Pasó
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: Solvencia Financiera & Presupuesto                               │
│ ¿Hay saldo suficiente en la cuenta Blinka y presupuesto en el periodo?   │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ No / Pasó
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: Gobierno Human-in-the-Loop (HITL)                                │
│ ¿Excede el límite autónomo ($2,000 USD) o es un proveedor nuevo?        │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
    [ AUTO_APPROVED ]       [ SCALED_TO_HUMAN ]          [ REJECTED ]
   (Pago Aprobado 100%)    (Requiere Humano)         (Frenado / Rechazado)
```

---

## 4. Matriz Completa de Reglas de Negocio

### Capa 1: Compliance y Prevención SARLAFT (Colombia & LatAm)

> **Objetivo:** Evitar transacciones con personas o entidades sancionadas, respetando el marco SARLAFT para la gestión del riesgo de lavado de activos y financiación del terrorismo.

| Código | Nombre de la Regla | Condición Lógica | Decisión | Razón / Explicación Registrada |
| :--- | :--- | :--- | :--- | :--- |
| **COMP-01** | **Listas Restrictivas (OFAC/ONU)** | Beneficiario registrado en OFAC, ONU o listas de sanciones GAFI. | `REJECTED` | *Rechazado por coincidencia con lista restrictiva internacional.* |
| **COMP-02** | **Cuentas Bancarias No Permitidas** | Las instrucciones de transferencia difieren de las cuentas validadas del proveedor. | `SCALED_TO_HUMAN` | *Instrucciones bancarias no coinciden con las cuentas autorizadas.* |
| **COMP-03** | **Alerta PEP (Políticamente Expuesto)** | El beneficiario o representante figura en el registro PEP. | `SCALED_TO_HUMAN` | *Escalado a Oficial de Cumplimiento por condición PEP.* |
| **COMP-04** | **Consistencia Identificación Fiscal** | NIT / RUT en la factura no coincide con la razón social registrada. | `SCALED_TO_HUMAN` | *Inconsistencia entre el NIT impreso y el registro fiscal.* |

---

### Capa 2: Integridad de la Factura y Verificación de Datos

> **Objetivo:** Prevenir pagos por cobros duplicados, errores de extracción de datos o facturas alteradas.

| Código | Nombre de la Regla | Condición Lógica | Decisión | Razón / Explicación Registrada |
| :--- | :--- | :--- | :--- | :--- |
| **INTEG-01** | **Detección de Cobro Duplicado** | Mismo ID Factura + Proveedor O mismo Monto + Proveedor en < 30 días. | `REJECTED` | *Factura rechazada por detección de cobro duplicado.* |
| **INTEG-02** | **Desviación de Tarifa Pactada** | Monto cobrado en la factura > Monto acordado en contrato/PO. | `SCALED_TO_HUMAN` | *El valor cobrado supera la tarifa acordada en el contrato.* |
| **INTEG-03** | **Calidad de Extracción (OCR/LLM)** | Confidence score en lectura de datos de la factura < 85%. | `SCALED_TO_HUMAN` | *Lectura de factura ambigua o ilegible. Requiere revisión.* |

---

### Capa 3: Solvencia Financiera y Presupuesto

> **Objetivo:** Garantizar la disponibilidad de liquidez en la cuenta de Blinka y el respeto a los techos presupuestales.

| Código | Regla | Condición Lógica | Decisión | Razón / Explicación Registrada |
| :--- | :--- | :--- | :--- | :--- |
| **FIN-01** | **Verificación de Saldo Existente** | `Monto Factura > Saldo Cuenta Blinka` (USD o Moneda Local). | `SCALED_TO_HUMAN` | *Saldo insuficiente en la cuenta Blinka para ejecutar el pago.* |
| **FIN-02** | **Tope Presupuestal del Período** | Acumulado de pagos del mes + Monto Factura > Presupuesto Asignado. | `SCALED_TO_HUMAN` | *El pago excede el presupuesto disponible del período.* |

---

### Capa 4: Umbrales y Gobierno Human-in-the-Loop (HITL)

> **Objetivo:** Detener la autonomía cuando se superen los niveles de riesgo aceptados por la administración.

| Código | Regla | Condición Lógica | Decisión | Razón / Explicación Registrada |
| :--- | :--- | :--- | :--- | :--- |
| **HITL-01** | **Monto Máximo de Aprobación Autónoma** | `Monto Factura > $2,000 USD` (Umbral configurable). | `SCALED_TO_HUMAN` | *El monto excede el límite autónomo de $2,000 USD.* |
| **HITL-02** | **Proveedor Nuevo (Primer Pago)** | El proveedor no cuenta con historial de pagos en la plataforma. | `SCALED_TO_HUMAN` | *Proveedor nuevo. Requiere verificación inicial por un operador.* |
| **HITL-03** | **Ambigüedad Acumulada** | Presencia de 2 o más pequeñas alertas de inconsistencia en la factura. | `SCALED_TO_HUMAN` | *Acumulación de pequeñas inconsistencias detectadas.* |

---

## 5. Matriz de Casos de Prueba Simulados (Test Suite Obligatorio)

Como la hackathon no otorga una API ni facturas reales, construimos un set de datos simulado que cubre los casos normales y los **casos trampa obligatorios**:

| ID Caso | Descripción del Caso de Prueba | Tipo de Caso | Resultado Esperado | Regla Disparada |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Factura mensual recurrente de AWS ($450 USD) con saldo suficiente y proveedor frecuente. | Normal | `AUTO_APPROVED` | Ninguna (Pasó 100%) |
| **TC-02** | Factura enviada por segunda vez en la misma semana ($1,200 USD). | **Trampa (Duplicado)** | `REJECTED` | `INTEG-01` |
| **TC-03** | Factura de proveedor nuevo no registrado previamente ($800 USD). | **Trampa (Proveedor Nuevo)** | `SCALED_TO_HUMAN` | `HITL-02` |
| **TC-04** | Factura con monto superior al pactado ($3,500 USD vs $2,000 USD de límite). | **Trampa (Monto Alto)** | `SCALED_TO_HUMAN` | `HITL-01` |
| **TC-05** | Factura por $10,000 USD cuando el saldo en Blinka es de $4,000 USD. | **Trampa (Saldo Insuficiente)** | `SCALED_TO_HUMAN` | `FIN-01` |
| **TC-06** | Factura con destino a cuenta bancaria en lista restrictiva OFAC. | **Trampa (Compliance)** | `REJECTED` | `COMP-01` |

---

## 6. Estructura del Registro de Decisiones (Audit Log JSON)

Cada evaluación produce un objeto JSON que alimenta directamente la interfaz web para garantizar la **explicabilidad total**:

```json
{
  "invoice_id": "INV-2026-104",
  "vendor_name": "DevStudio LatAm S.A.S.",
  "tax_id": "900.584.112-4",
  "amount": 2500.00,
  "currency": "USD",
  "issue_date": "2026-10-16",
  "due_date": "2026-10-31",
  "decision": "SCALED_TO_HUMAN",
  "confidence_score": 0.98,
  "evaluations": {
    "sarlaft_check": { "status": "PASSED", "blacklist_match": false },
    "duplicate_check": { "status": "PASSED", "is_duplicate": false },
    "balance_check": { "status": "PASSED", "current_balance_usd": 12000.00 },
    "hitl_check": {
      "status": "TRIGGERED",
      "reason_code": "HITL-01",
      "message": "El monto de $2,500.00 USD excede el límite autónomo de $2,000.00 USD."
    }
  },
  "explanation_for_ui": "El pago fue escalado a revisión humana porque el monto ($2,500.00 USD) supera el umbral autónomo permitido ($2,000.00 USD)."
}
```

---

## 7. Entregables del Repositorio (`/docs`)

Guarda este archivo en tu repositorio bajo la ruta:
`docs/reglas_pago_agente_v2.md`

Este documento sirve como arquitectura lógica para el desarrollo y como el corazón del **Playbook de Presentación** para el Demo Day ante el jurado de Blinka y 30X.
