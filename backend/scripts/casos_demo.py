"""
Casos de demostración TC-01..TC-07 sobre el seed (DB_SEED_DEMO=true) y las reglas por defecto.
Fuente única para tests/test_postgres_integration.py y scripts/humo_produccion.py.
Cada caso: (id, decision_status esperado, regla que debe aparecer en audit_explanation o None, payload).

Antes de TC-01 se toma una foto del saldo con PATCH /api/treasury y SALDO_DEMO_USD (Fase 6): así lo aprobado
en corridas anteriores deja de comprometer el saldo y TC-01 no escala por FIN-01/FIN-03.
"""

# Saldo del seed (treasury_accounts): TC-05 lo supera
SALDO_DEMO_USD = 8500.00

CASOS = [
    ("TC-01", "AUTO_APPROVED", None, {
        "invoice_number": "AWS-2026-10", "vendor_name": "Amazon Web Services LATAM",
        "vendor_tax_id": "US-91-1646860", "original_amount": 450}),
    ("TC-02", "REJECTED", "INTEG-01", {
        "invoice_number": "DS-1042", "vendor_name": "DevStudio LatAm S.A.S.",
        "vendor_tax_id": "900.584.112-4", "original_amount": 5040000, "original_currency": "COP"}),
    ("TC-03", "SCALED_TO_HUMAN", "HITL-02", {
        "invoice_number": "DC-001", "vendor_name": "Diseño Creativo Bogotá S.A.S.", "original_amount": 800}),
    ("TC-04", "SCALED_TO_HUMAN", "HITL-01", {
        "invoice_number": "NA-090", "vendor_name": "Nube Andina Consultores S.A.S.",
        "vendor_tax_id": "901.223.450-1", "original_amount": 3500}),
    ("TC-05", "SCALED_TO_HUMAN", "FIN-01", {
        "invoice_number": "LEM-3400", "vendor_name": "Logística Express MX S.A. de C.V.",
        "vendor_tax_id": "LEM850101AB1", "original_amount": 195000, "original_currency": "MXN"}),
    ("TC-06", "REJECTED", "COMP-01", {
        "invoice_number": "GTP-01", "vendor_name": "Global Trade Partners Ltd",
        "vendor_tax_id": "PA-155-7788", "bank_account": "PA-BANCO-PACIFICO-998877", "original_amount": 900}),
    # No cuadra con lo acordado: proveedor frecuente, bajo el umbral autónomo, pero sobre su tarifa pactada ($1,000)
    ("TC-07", "SCALED_TO_HUMAN", "INTEG-02", {
        "invoice_number": "AWS-2026-10-EXTRA", "vendor_name": "Amazon Web Services LATAM",
        "vendor_tax_id": "US-91-1646860", "original_amount": 1500}),
]
