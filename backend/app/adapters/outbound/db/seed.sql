-- ==============================================================================
-- BLINKA PAYAGENT - DATOS SEED DE DEMOSTRACIÓN
-- Preparados para disparar la Test Suite TC-01 a TC-06 (docs/reglas-negocio/reglas_pago_agente_v3.md).
-- Idempotente: no duplica filas si se ejecuta varias veces.
-- ==============================================================================

-- Reglas por defecto
INSERT INTO company_rules (company_id, max_autonomous_usd, sarlaft_check_enabled, duplicate_check_days, min_treasury_buffer_usd)
VALUES ('BLINKA_DEFAULT', 2000.00, TRUE, 30, 1000.00)
ON CONFLICT (company_id) DO NOTHING;

-- Tesorería: $8,500 USD de saldo (TC-05 lo supera) y $25,000 USD de presupuesto mensual
INSERT INTO treasury_accounts (company_id, balance_usd, monthly_budget_usd)
VALUES ('BLINKA_DEFAULT', 8500.00, 25000.00)
ON CONFLICT (company_id) DO NOTHING;

-- Proveedores verificados
INSERT INTO vendors (tax_id, legal_name, bank_account, is_pep, contract_amount_usd) VALUES
    ('US-91-1646860',  'Amazon Web Services LATAM',          'US-CHASE-000123456',          FALSE, 1000.00),   -- TC-01
    ('900.584.112-4',  'DevStudio LatAm S.A.S.',             'CO-BANCOLOMBIA-11122233344',  FALSE, 1500.00),   -- TC-02
    ('901.223.450-1',  'Nube Andina Consultores S.A.S.',     'CO-DAVIVIENDA-55566677788',   FALSE, 5000.00),   -- TC-04
    ('LEM850101AB1',   'Logística Express MX S.A. de C.V.',  'MX-BBVA-012180001234567890',  FALSE, 15000.00),  -- TC-05
    ('PA-155-7788',    'Global Trade Partners Ltd',          'PA-BANCO-PACIFICO-998877',    FALSE, 3000.00),   -- TC-06
    ('900.777.321-9',  'Consultora Riesgo Político S.A.S.',  'CO-BOGOTA-99988877766',       TRUE,  2000.00)    -- PEP (COMP-03)
ON CONFLICT (tax_id) DO NOTHING;

-- Listas restrictivas
INSERT INTO sanctions_list (list_source, entity_name, tax_id, bank_account) VALUES
    ('OFAC', 'Global Trade Partners Ltd', 'PA-155-7788', 'PA-BANCO-PACIFICO-998877'),  -- TC-06
    ('ONU',  'Inversiones Sombra S.A.',   NULL,          'VE-BANCO-SOMBRA-000111')
ON CONFLICT (list_source, entity_name) DO NOTHING;

-- Historial de pagos (solo si la tabla está vacía): da antigüedad a los proveedores (HITL-02)
-- y deja una factura reciente de DevStudio para el caso de duplicado (TC-02).
INSERT INTO invoices (invoice_number, vendor_name, vendor_tax_id, original_amount, original_currency,
                      fx_rate_applied, usd_amount, channel_source, decision_status, audit_explanation,
                      bank_account, ocr_confidence_score, processed_at)
SELECT * FROM (VALUES
    ('AWS-2026-08', 'Amazon Web Services LATAM', 'US-91-1646860', 450.00, 'USD', 1.0, 450.00, 'TELEGRAM',
     'AUTO_APPROVED', 'Pago aprobado automáticamente: proveedor verificado, monto dentro del límite autónomo y saldo suficiente.',
     'US-CHASE-000123456', 0.990, NOW() - INTERVAL '45 days'),
    ('DS-1041', 'DevStudio LatAm S.A.S.', '900.584.112-4', 5040000.00, 'COP', 4200.0, 1200.00, 'TELEGRAM',
     'AUTO_APPROVED', 'Pago aprobado automáticamente: $1,200.00 USD ($5,040,000 COP a tasa 4,200 COP/USD) dentro del límite autónomo.',
     'CO-BANCOLOMBIA-11122233344', 0.970, NOW() - INTERVAL '40 days'),
    ('DS-1042', 'DevStudio LatAm S.A.S.', '900.584.112-4', 5040000.00, 'COP', 4200.0, 1200.00, 'TELEGRAM',
     'AUTO_APPROVED', 'Pago aprobado automáticamente: $1,200.00 USD ($5,040,000 COP a tasa 4,200 COP/USD) dentro del límite autónomo.',
     'CO-BANCOLOMBIA-11122233344', 0.980, NOW() - INTERVAL '3 days'),
    ('NA-077', 'Nube Andina Consultores S.A.S.', '901.223.450-1', 1800.00, 'USD', 1.0, 1800.00, 'API',
     'AUTO_APPROVED', 'Pago aprobado automáticamente: proveedor verificado y monto dentro del límite autónomo.',
     'CO-DAVIVIENDA-55566677788', 1.000, NOW() - INTERVAL '50 days'),
    ('LEM-3301', 'Logística Express MX S.A. de C.V.', 'LEM850101AB1', 117000.00, 'MXN', 19.5, 6000.00, 'TELEGRAM',
     'HUMAN_APPROVED', 'Escalado por superar el límite autónomo de $2,000.00 USD. Aprobado por el CFO desde el dashboard.',
     'MX-BBVA-012180001234567890', 0.950, NOW() - INTERVAL '35 days')
) AS seed(invoice_number, vendor_name, vendor_tax_id, original_amount, original_currency, fx_rate_applied,
          usd_amount, channel_source, decision_status, audit_explanation, bank_account, ocr_confidence_score, processed_at)
WHERE NOT EXISTS (SELECT 1 FROM invoices);
