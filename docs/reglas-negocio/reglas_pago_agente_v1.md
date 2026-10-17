# Políticas y Reglas de Negocio para el Agente de Pagos (Blinka - Hackathon 30X)

## 1. Visión General del Agente
El **Agente de Pagos de Blinka** es una solución automatizada diseñada para procesar facturas y cuentas de cobro de empresas globales que operan en Latinoamérica. Su objetivo es tomar decisiones autónomas sobre cada obligación financiera recibida, clasificándola en uno de tres estados deterministas:

* **`AUTO_APPROVED` (Aprobado):** Cumple con el 100% de los criterios de seguridad, cumplimiento (SARLAFT), presupuesto y consistencia de datos.
* **`SCALED_TO_HUMAN` (Escalado / Human-in-the-Loop):** Presenta incertidumbre, falta de soporte, umbral alto de riesgo o supera límites configurados. Requiere acción explícita de un operador financiero.
* **`REJECTED` (Rechazado / Frenado):** Viola directamente políticas de seguridad, SARLAFT, intentos de cobro duplicado o fraudes detectados.

---

## 2. Flujo de Decisión en 4 Capas (Pipeline de Evaluación)

Cada factura procesada por el agente debe atravesar secuencialmente cuatro capas de validación lógica antes de emitir un dictamen final:

```
[ Factura Entrada ]
        │
        ▼
┌──────────────────────────────┐
│ 1. Capa SARLAFT & Compliance │ ── (Riesgo Alto / Lista Negra) ──► [ REJECTED ]
└──────────────┬───────────────┘
               │ Pass / Low Risk
               ▼
┌──────────────────────────────┐
│ 2. Capa Integridad & Matches │ ── (Factura Duplicada / Inconsistente) ──► [ REJECTED / SCALED ]
└──────────────┬───────────────┘
               │ Pass
               ▼
┌──────────────────────────────┐
│ 3. Capa Financiera & Saldo   │ ── (Sin Saldo / Excede Presupuesto) ──► [ SCALED_TO_HUMAN ]
└──────────────┬───────────────┘
               │ Pass
               ▼
┌──────────────────────────────┐
│ 4. Capa HITL & Umbrales      │ ── (Monto > Límite / Proveedor Nuevo) ─► [ SCALED_TO_HUMAN ]
└──────────────┬───────────────┘
               │ Pass (100% Criterios Ok)
               ▼
      [ AUTO_APPROVED ]
```

---

## 3. Matriz de Reglas de Negocio

### Capa 1: Compliance y Prevención SARLAFT (Colombia & LatAm)

> **Objetivo:** Garantizar que la empresa no realice transacciones con personas o entidades sancionadas, ni incurra en riesgos de Lavado de Activos o Financiación del Terrorismo.

| Código Regla | Nombre de la Regla | Condición Evaluada | Acción / Estado |
| :--- | :--- | :--- | :--- |
| **COMP-01** | **Listas Restrictivas Internacionales** | Beneficiario registrado en OFAC (Lista Clinton), ONU, UE o Listas de Sanciones. | `REJECTED` (Bloqueo automático e inmediato). |
| **COMP-02** | **Cotejo de Identificación (RUT / NIT)** | El NIT/RUT del beneficiario no coincide con la razón social en la factura o la base de datos oficial (DIAN). | `SCALED_TO_HUMAN` (Motivo: Inconsistencia en identificación fiscal). |
| **COMP-03** | **Personas Expuestas Políticamente (PEP)** | El beneficiario o representante legal está clasificado como PEP. | `SCALED_TO_HUMAN` (Requiere aprobación de Oficial de Cumplimiento). |
| **COMP-04** | **Cambio Repentino de Cuenta Bancaria** | Las instrucciones de pago difieren de las cuentas históricamente registradas y validadas del proveedor. | `SCALED_TO_HUMAN` (Alerta de posible suplantación / cambio de cuenta). |
| **COMP-05** | **Jurisdicciones de Alto Riesgo** | El pago se solicita hacia o desde un país en lista gris/negra GAFI (FATF). | `REJECTED` o `SCALED_TO_HUMAN` según política corporativa. |

---

### Capa 2: Integridad de la Factura y Verificación de Servicio/Entrega

> **Objetivo:** Prevenir pagos por servicios no prestados, cobros duplicados o errores en la extracción de datos.

| Código Regla | Nombre de la Regla | Condición Evaluada | Acción / Estado |
| :--- | :--- | :--- | :--- |
| **INTEG-01** | **Detección de Cobro Duplicado** | Mismo número de factura + mismo proveedor O mismo monto + mismo proveedor en un lapso < 30 días. | `REJECTED` (Motivo: Factura o transacción duplicada). |
| **INTEG-02** | **Cotejo con Orden de Compra / Contrato** | El monto, concepto o ítems no coinciden con la Orden de Compra (PO) o tarifa pactada en contrato. | `SCALED_TO_HUMAN` (Discrepancia en contrato o monto acordado). |
| **INTEG-03** | **Confirmación de Entrega (3-Way Match)** | No existe registro de recepción conforme del bien/servicio por parte del área solicitante. | `SCALED_TO_HUMAN` (Pendiente de confirmación de recepción). |
| **INTEG-04** | **Confianza de Extracción (OCR / LLM)** | El score de confianza de la extracción automática de datos es `< 85%`. | `SCALED_TO_HUMAN` (Baja confianza en lectura de datos). |

---

### Capa 3: Disponibilidad Financiera y Presupuesto

> **Objetivo:** Asegurar la solvencia de la cuenta y respetar los topes de presupuesto de la empresa.

| Código Regla | Nombre de la Regla | Condición Evaluada | Acción / Estado |
| :--- | :--- | :--- | :--- |
| **FIN-01** | **Verificación de Saldo Disponible** | `Monto Factura > Saldo Cuenta Blinka` (USD o Moneda Local). | `SCALED_TO_HUMAN` (Motivo: Saldo insuficiente para ejecutar el pago). |
| **FIN-02** | **Límite de Presupuesto Mensual** | El pago supera el presupuesto asignado al centro de costos o departamento para el periodo actual. | `SCALED_TO_HUMAN` (Supera presupuesto departamental). |
| **FIN-03** | **Límite de Pagos por Proveedor** | Acumulado de pagos al mismo proveedor en el mes excede el tope pre-aprobado. | `SCALED_TO_HUMAN` (Exceso de tope mensual por proveedor). |

---

### Capa 4: Umbrales y Gobierno Human-in-the-Loop (HITL)

> **Objetivo:** Definir cuándo la autonomía del agente se detiene para dejar el control final a un operador humano.

| Código Regla | Nombre de la Regla | Condición Evaluada | Acción / Estado |
| :--- | :--- | :--- | :--- |
| **HITL-01** | **Monto Máximo de Aprobación Autónoma** | `Monto Factura > $2,000 USD` (configurable por empresa). | `SCALED_TO_HUMAN` (Requiere firma/aprobación de Gerente Financiero). |
| **HITL-02** | **Proveedor Nuevo (Primer Pago)** | Es la primera transacción realizada con este proveedor en la plataforma. | `SCALED_TO_HUMAN` (Validación inicial de proveedor nuevo). |
| **HITL-03** | **Incertidumbre Combinada / Ambigüedad** | Múltiples alertas leves de riesgo que sumadas superan el umbral de tolerancia. | `SCALED_TO_HUMAN` (Puntaje de ambigüedad acumulado). |

---

## 4. Estructura del Registro de Decisiones (Audit Log JSON)

El reto de Blinka exige que cada decisión sea **100% explicable**. El agente debe generar para cada factura una trazabilidad estructurada en formato JSON:

```json
{
  "invoice_id": "INV-2026-089",
  "vendor_name": "Servicios Tech LatAm S.A.S.",
  "tax_id": "901.234.567-8",
  "amount": 1850.00,
  "currency": "USD",
  "issue_date": "2026-10-15",
  "due_date": "2026-10-30",
  "decision": "SCALED_TO_HUMAN",
  "confidence_score": 0.96,
  "evaluations": {
    "sarlaft_check": {
      "status": "PASSED",
      "pep_detected": false,
      "blacklist_match": false
    },
    "duplicate_check": {
      "status": "PASSED",
      "is_duplicate": false
    },
    "balance_check": {
      "status": "PASSED",
      "current_balance_usd": 15000.00,
      "sufficient_balance": true
    },
    "hitl_check": {
      "status": "TRIGGERED",
      "reason_code": "HITL-02",
      "message": "Es la primera vez que se procesa un pago para este proveedor. Se requiere verificación humana inicial."
    }
  },
  "explanation_for_ui": "El pago por $1,850.00 USD cumple con las políticas de SARLAFT y saldo en cuenta. Sin embargo, se escaló a aprobación humana porque 'Servicios Tech LatAm S.A.S.' es un proveedor nuevo en el sistema."
}
```

---

## 5. Guía de Implementación para el Repositorio (`/docs`)

Guarda este archivo en tu repositorio bajo la ruta:
`docs/reglas_pago_agente.md`

Este documento servirá como **especificación técnica para el equipo** y como soporte fundamental para el **Playbook / Presentación del Demo Day**, demostrando el rigor en gobierno corporativo, seguridad y cumplimiento SARLAFT que exige Blinka.
