"""
Adaptador de Salida: PostgreSQL (asyncpg)
Implementa InvoiceRepository, RulesRepository, VendorRepository, SanctionsRepository y TreasuryRepository
sobre las tablas definidas en schema.sql.
"""

import json
from dataclasses import fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import asyncpg

from app.core.domain.models import CompanyRules, DecisionStatus, ProcessedInvoice, TreasuryStatus, Vendor

SQL_DIR = Path(__file__).parent
APPROVED = (DecisionStatus.AUTO_APPROVED.value, DecisionStatus.HUMAN_APPROVED.value)
NOT_REJECTED = (
    DecisionStatus.AUTO_APPROVED.value,
    DecisionStatus.SCALED_TO_HUMAN.value,
    DecisionStatus.HUMAN_APPROVED.value,
)
# Coincidencia de proveedor por NIT o por razón social (cuando el OCR no trae NIT)
VENDOR_MATCH = "((vendor_tax_id IS NOT NULL AND vendor_tax_id = $1) OR lower(vendor_name) = lower($2))"


class DatabaseUnavailableError(RuntimeError):
    """Se intentó usar la base de datos sin DATABASE_URL o sin conexión."""


class PostgresDatabase:
    """Pool de conexiones compartido por los repositorios."""

    def __init__(self, database_url: Optional[str]):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, auto_migrate: bool = False, seed_demo: bool = False) -> None:
        if not self.database_url:
            return
        self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5, init=self._init_conn)
        async with self.pool.acquire() as conn:
            if auto_migrate:
                await conn.execute((SQL_DIR / "schema.sql").read_text())
            if seed_demo:
                await conn.execute((SQL_DIR / "seed.sql").read_text())

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    def require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise DatabaseUnavailableError("Base de datos no disponible: configura DATABASE_URL en el .env raíz.")
        return self.pool

    @staticmethod
    async def _init_conn(conn: asyncpg.Connection) -> None:
        await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


def _row_to_invoice(row: asyncpg.Record) -> ProcessedInvoice:
    data = {f.name: row[f.name] for f in fields(ProcessedInvoice) if f.name in row}
    for key in ("original_amount", "usd_amount", "fx_rate_applied", "ocr_confidence_score"):
        if data.get(key) is not None:
            data[key] = float(data[key])
    data["decision_status"] = DecisionStatus(data["decision_status"])
    data["evaluations"] = data.get("evaluations") or {}
    return ProcessedInvoice(**data)


class PostgresInvoiceRepository:
    """Repositorio de facturas y Audit Log."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def save(self, invoice: ProcessedInvoice) -> ProcessedInvoice:
        row = await self.db.require_pool().fetchrow(
            """
            INSERT INTO invoices (invoice_number, vendor_name, vendor_tax_id, bank_account, original_amount,
                original_currency, fx_rate_applied, usd_amount, due_date, ocr_confidence_score, channel_source,
                source_chat_id, decision_status, audit_explanation, evaluations, processed_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            RETURNING *
            """,
            invoice.invoice_number, invoice.vendor_name, invoice.vendor_tax_id, invoice.bank_account,
            invoice.original_amount, invoice.original_currency, invoice.fx_rate_applied, invoice.usd_amount,
            invoice.due_date, invoice.ocr_confidence_score, invoice.channel_source, invoice.source_chat_id,
            invoice.decision_status.value, invoice.audit_explanation, invoice.evaluations, invoice.processed_at,
        )
        return _row_to_invoice(row)

    async def get(self, invoice_id: int) -> Optional[ProcessedInvoice]:
        row = await self.db.require_pool().fetchrow("SELECT * FROM invoices WHERE id = $1", invoice_id)
        return _row_to_invoice(row) if row else None

    async def list_recent(self, limit: int = 50) -> List[ProcessedInvoice]:
        rows = await self.db.require_pool().fetch(
            "SELECT * FROM invoices ORDER BY processed_at DESC, id DESC LIMIT $1", limit
        )
        return [_row_to_invoice(r) for r in rows]

    async def update_decision(
        self, invoice_id: int, status: DecisionStatus, explanation: str,
        decided_by: str, decided_at: datetime, note: Optional[str], expected_status: DecisionStatus,
    ) -> Optional[ProcessedInvoice]:
        # El guard de estado va en el mismo UPDATE: si otro operador decidió primero, no se pisa
        row = await self.db.require_pool().fetchrow(
            """
            UPDATE invoices SET decision_status = $2, audit_explanation = $3, decided_by = $4,
                decided_at = $5, human_note = $6
            WHERE id = $1 AND decision_status = $7 RETURNING *
            """,
            invoice_id, status.value, explanation, decided_by, decided_at, note, expected_status.value,
        )
        return _row_to_invoice(row) if row else None

    async def exists_duplicate(
        self, vendor_tax_id: Optional[str], vendor_name: Optional[str],
        invoice_number: Optional[str], usd_amount: Optional[float], within_days: int,
    ) -> bool:
        since = datetime.utcnow() - timedelta(days=within_days)
        return await self.db.require_pool().fetchval(
            f"""
            SELECT EXISTS (SELECT 1 FROM invoices
                WHERE {VENDOR_MATCH} AND (invoice_number = $3 OR ($4::numeric IS NOT NULL AND usd_amount = $4))
                  AND processed_at >= $5 AND decision_status = ANY($6::text[]))
            """,
            vendor_tax_id, vendor_name or "", invoice_number,
            round(usd_amount, 2) if usd_amount is not None else None, since, list(NOT_REJECTED),
        )

    async def vendor_has_paid_history(self, vendor_tax_id: Optional[str], vendor_name: Optional[str]) -> bool:
        return await self.db.require_pool().fetchval(
            f"SELECT EXISTS (SELECT 1 FROM invoices WHERE {VENDOR_MATCH} AND decision_status = ANY($3::text[]))",
            vendor_tax_id, vendor_name or "", list(APPROVED),
        )

    async def sum_approved_usd_since(self, since: datetime) -> float:
        total = await self.db.require_pool().fetchval(
            "SELECT COALESCE(SUM(usd_amount), 0) FROM invoices WHERE processed_at >= $1 AND decision_status = ANY($2::text[])",
            since, list(APPROVED),
        )
        return float(total)


class PostgresRulesRepository:
    """Repositorio de reglas corporativas."""

    def __init__(self, db: PostgresDatabase, defaults: CompanyRules):
        self.db = db
        self.defaults = defaults

    async def get(self, company_id: str) -> CompanyRules:
        row = await self.db.require_pool().fetchrow(
            """SELECT company_id, max_autonomous_usd, sarlaft_check_enabled, duplicate_check_days,
                      min_treasury_buffer_usd FROM company_rules WHERE company_id = $1""",
            company_id,
        )
        if row is None:
            return self.defaults
        return CompanyRules(
            company_id=row["company_id"],
            max_autonomous_usd=float(row["max_autonomous_usd"]),
            sarlaft_check_enabled=row["sarlaft_check_enabled"],
            duplicate_check_days=row["duplicate_check_days"],
            min_treasury_buffer_usd=float(row["min_treasury_buffer_usd"]),
        )

    async def save(self, rules: CompanyRules) -> CompanyRules:
        await self.db.require_pool().execute(
            """
            INSERT INTO company_rules (company_id, max_autonomous_usd, sarlaft_check_enabled,
                duplicate_check_days, min_treasury_buffer_usd)
            VALUES ($1,$2,$3,$4,$5)
            ON CONFLICT (company_id) DO UPDATE SET max_autonomous_usd = EXCLUDED.max_autonomous_usd,
                sarlaft_check_enabled = EXCLUDED.sarlaft_check_enabled,
                duplicate_check_days = EXCLUDED.duplicate_check_days,
                min_treasury_buffer_usd = EXCLUDED.min_treasury_buffer_usd
            """,
            rules.company_id, rules.max_autonomous_usd, rules.sarlaft_check_enabled,
            rules.duplicate_check_days, rules.min_treasury_buffer_usd,
        )
        return rules


class PostgresVendorRepository:
    """Registro de proveedores verificados."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def find(self, tax_id: Optional[str], name: Optional[str]) -> Optional[Vendor]:
        row = await self.db.require_pool().fetchrow(
            """SELECT * FROM vendors WHERE tax_id = $1 OR lower(legal_name) = lower($2)
               ORDER BY (tax_id = $1) DESC NULLS LAST LIMIT 1""",
            tax_id, name or "",
        )
        if row is None:
            return None
        contract = row["contract_amount_usd"]
        return Vendor(
            tax_id=row["tax_id"], legal_name=row["legal_name"], bank_account=row["bank_account"],
            is_pep=row["is_pep"], contract_amount_usd=float(contract) if contract is not None else None,
        )


class PostgresSanctionsRepository:
    """Listas restrictivas OFAC / ONU / GAFI."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def find_match(
        self, name: Optional[str], tax_id: Optional[str], bank_account: Optional[str]
    ) -> Optional[str]:
        row = await self.db.require_pool().fetchrow(
            """SELECT list_source, entity_name FROM sanctions_list
               WHERE lower(entity_name) = lower($1) OR tax_id = $2 OR bank_account = $3 LIMIT 1""",
            name or "", tax_id, bank_account,
        )
        return f"{row['list_source']}: {row['entity_name']}" if row else None


class PostgresTreasuryRepository:
    """Saldo y presupuesto de la cuenta Blinka."""

    def __init__(self, db: PostgresDatabase, defaults: TreasuryStatus):
        self.db = db
        self.defaults = defaults

    async def get(self, company_id: str) -> TreasuryStatus:
        row = await self.db.require_pool().fetchrow(
            "SELECT balance_usd, monthly_budget_usd FROM treasury_accounts WHERE company_id = $1", company_id
        )
        if row is None:
            return TreasuryStatus(self.defaults.balance_usd, self.defaults.monthly_budget_usd)
        return TreasuryStatus(float(row["balance_usd"]), float(row["monthly_budget_usd"]))
