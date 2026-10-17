-- ==============================================================================
-- BLINKA PAYAGENT - ESQUEMA DE BASE DE DATOS POSTGRESQL (Railway)
-- Arquitectura de Solución v4
-- ==============================================================================

-- 1. Tabla de Reglas de Negocio Corporativas
CREATE TABLE IF NOT EXISTS company_rules (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    max_autonomous_usd NUMERIC(12,2) DEFAULT 2000.00,
    sarlaft_check_enabled BOOLEAN DEFAULT TRUE,
    duplicate_check_days INT DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserción de configuración por defecto para Blinka
INSERT INTO company_rules (company_id, max_autonomous_usd, sarlaft_check_enabled, duplicate_check_days)
VALUES ('BLINKA_DEFAULT', 2000.00, TRUE, 30)
ON CONFLICT DO NOTHING;

-- 2. Tabla Principal de Facturas y Cuentas de Cobro
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_name VARCHAR(150) NOT NULL,
    vendor_tax_id VARCHAR(50),
    original_amount NUMERIC(14,2) NOT NULL,
    original_currency VARCHAR(10) NOT NULL,
    fx_rate_applied NUMERIC(10,4),
    usd_amount NUMERIC(12,2) NOT NULL,
    due_date DATE,
    channel_source VARCHAR(30) DEFAULT 'TELEGRAM',
    decision_status VARCHAR(30) NOT NULL, -- 'AUTO_APPROVED', 'SCALED_TO_HUMAN', 'REJECTED'
    audit_explanation TEXT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar búsquedas de duplicados y filtros en Audit Log
CREATE INDEX IF NOT EXISTS idx_invoices_vendor_number ON invoices(vendor_tax_id, invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_decision_status ON invoices(decision_status);
CREATE INDEX IF NOT EXISTS idx_invoices_processed_at ON invoices(processed_at DESC);
