# Misión — Blinka PayAgent (Paybot)

> Parte de la constitución del proyecto, junto con [tech-stack.md](tech-stack.md) y [roadmap.md](roadmap.md).
> Si un cambio contradice este documento, se actualiza primero este documento o se descarta el cambio.

## Misión

Eliminar el trabajo manual y el riesgo de pagar facturas de proveedores en Latinoamérica para empresas globales con cuenta en Blinka: un agente que **lee, convierte, evalúa y explica** cada factura en segundos, decide solo cuando es seguro y escala a una persona cuando no lo es.

## Problema

Las empresas constituidas en EE. UU. con equipos y proveedores en LatAm reciben decenas de cuentas de cobro al mes, en varias monedas, por correo, PDF o chat. Hoy alguien las transcribe, convierte y valida a mano: es lento, inconsistente y deja la puerta abierta a duplicados, fraudes y pagos fuera de política.

## Para quién

| Usuario | Qué necesita |
| :--- | :--- |
| **Equipo operativo / proveedores** | Enviar una factura (foto o PDF) por el canal que ya usan y saber qué pasó con ella. |
| **Aprobador financiero (CFO, tesorería)** | Revisar solo las excepciones, con la razón clara, y decidir en el dashboard. |
| **Auditor / cumplimiento** | Entender por qué se pagó, frenó o escaló cada factura sin leer código. |

## Principios no negociables

1. **Tolerancia cero:** nunca se aprueba un pago fuera de las reglas. Ante la duda (datos ilegibles, moneda desconocida, falta de saldo o de datos de tesorería), la factura **escala**; nunca se aprueba por defecto.
2. **Decisiones deterministas:** la IA solo extrae datos. La decisión la toma la tubería de 4 capas (Compliance/SARLAFT, Integridad, Solvencia, Gobierno HITL) definida en [reglas_pago_agente_v3.md](../docs/reglas-negocio/reglas_pago_agente_v3.md).
3. **Explicabilidad total:** cada decisión queda en el Audit Log con la regla disparada (código) y una explicación en lenguaje natural, capa por capa.
4. **Los canales solo ingresan facturas:** Telegram, la subida web y los canales futuros reciben facturas e informan resultados. La aprobación humana ocurre **únicamente en el dashboard** y queda registrada (`HUMAN_APPROVED` / `HUMAN_REJECTED`, quién y cuándo).
5. **$0.00 FX Markup:** los umbrales, el presupuesto y los reportes se expresan en USD. La solvencia se evalúa contra la billetera de la moneda de la factura y, si no alcanza, contra USD convertido sin markup. La billetera usada, la tasa y su fuente quedan explícitas en el registro.

## Alcance del MVP (Hackathon 30X — entrega domingo 18 de octubre de 2026, 11:59 AM hora de Colombia)

**Entra:**
- Ingesta por Telegram y por subida de archivos en el dashboard.
- Extracción multimodal con Gemini (OCR estructurado).
- Tesorería multimoneda con billeteras por moneda y conversión a USD con tasas en vivo, con tasas de referencia fijas como respaldo.
- Inicio de sesión con roles de demo (operador y aprobador) para las acciones que cambian datos.
- Tubería de 4 capas con la matriz de reglas v3 y decisión `AUTO_APPROVED` / `SCALED_TO_HUMAN` / `REJECTED`.
- Aprobación humana en el dashboard y aviso al canal de origen.
- Audit Log explicable y reglas configurables desde el dashboard.
- Test Suite TC-01 a TC-06 demostrable con datos ficticios.

**No entra (por definición del reto):**
- Ejecutar pagos reales o mover dinero.
- Abrir cuentas bancarias o hacer KYB / verificación compleja de identidad.
- Motores complejos de fraude bancario.
- Rediseñar la app de Blinka.

## Visión de producto (después del Demo Day)

Aspiraciones, no compromisos del MVP:
- **Más canales de ingesta:** correo electrónico y WhatsApp, con el mismo caso de uso y las mismas reglas.
- **Datos vivos:** tasas de cambio en tiempo real, saldo y movimientos leídos de la cuenta Blinka, listas restrictivas actualizadas automáticamente.
- **Multiempresa:** reglas, proveedores y tesorería por empresa, con roles de aprobador.
- **Ejecución de pagos vía Blinka:** una vez aprobada, la factura se programa como pago desde la cuenta Blinka, manteniendo el mismo Audit Log.
- **Contratos y órdenes de compra:** cargar tarifas pactadas por proveedor para fortalecer INTEG-02.

## Cómo medimos el éxito

| Criterio | Meta |
| :--- | :--- |
| **Autonomía** | % de facturas resueltas sin intervención humana (`AUTO_APPROVED` + `REJECTED` sobre el total). Las decisiones `HUMAN_*` no cuentan como autónomas. |
| **Seguridad** | Cero pagos aprobados fuera de las reglas. Los seis casos de la Test Suite dan siempre el resultado esperado. |
| **Explicabilidad** | Cualquier operador entiende la decisión leyendo solo el Audit Log. |
| **Viabilidad** | Demo pública desplegada en Railway, con el repositorio respaldando exactamente lo que se muestra. |
