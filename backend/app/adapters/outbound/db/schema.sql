-- ==============================================================================
-- BLINKA PAYAGENT - ESQUEMA DE BASE DE DATOS POSTGRESQL (Railway)
-- Arquitectura de Solución v4
-- Idempotente: puede ejecutarse en cada arranque (DB_AUTO_MIGRATE=true).
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
ALTER TABLE company_rules ADD COLUMN IF NOT EXISTS min_treasury_buffer_usd NUMERIC(12,2) DEFAULT 1000.00;
CREATE UNIQUE INDEX IF NOT EXISTS uq_company_rules_company_id ON company_rules(company_id);

-- 2. Tesorería: saldo de la cuenta Blinka en USD y presupuesto mensual (Capa 3)
CREATE TABLE IF NOT EXISTS treasury_accounts (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL UNIQUE,
    balance_usd NUMERIC(14,2) NOT NULL,
    monthly_budget_usd NUMERIC(14,2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Registro de proveedores verificados (Capas 1, 2 y 4)
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    tax_id VARCHAR(50) NOT NULL UNIQUE,
    legal_name VARCHAR(150) NOT NULL,
    bank_account VARCHAR(80),               -- Cuenta autorizada (COMP-02)
    is_pep BOOLEAN DEFAULT FALSE,           -- Persona Expuesta Políticamente (COMP-03)
    contract_amount_usd NUMERIC(12,2),      -- Tarifa pactada en contrato/PO (INTEG-02)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Listas restrictivas OFAC / ONU / GAFI (COMP-01)
CREATE TABLE IF NOT EXISTS sanctions_list (
    id SERIAL PRIMARY KEY,
    list_source VARCHAR(20) NOT NULL,       -- 'OFAC', 'ONU', 'GAFI'
    entity_name VARCHAR(150) NOT NULL,
    tax_id VARCHAR(50),
    bank_account VARCHAR(80),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sanctions_entity ON sanctions_list(list_source, entity_name);

-- 5. Tabla Principal de Facturas y Cuentas de Cobro (Audit Log)
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
    -- 'AUTO_APPROVED', 'SCALED_TO_HUMAN', 'REJECTED', 'HUMAN_APPROVED', 'HUMAN_REJECTED'
    decision_status VARCHAR(30) NOT NULL,
    audit_explanation TEXT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS bank_account VARCHAR(80);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ocr_confidence_score NUMERIC(4,3);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS evaluations JSONB DEFAULT '{}'::jsonb;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS source_chat_id BIGINT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS decided_by VARCHAR(100);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS decided_at TIMESTAMP;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS human_note TEXT;

-- Índices para optimizar búsquedas de duplicados y filtros en Audit Log
CREATE INDEX IF NOT EXISTS idx_invoices_vendor_number ON invoices(vendor_tax_id, invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_decision_status ON invoices(decision_status);
CREATE INDEX IF NOT EXISTS idx_invoices_processed_at ON invoices(processed_at DESC);
