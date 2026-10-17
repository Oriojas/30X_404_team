"""
Adaptador de Salida: PostgreSQL (asyncpg)
Implementa InvoiceRepository, RulesRepository, VendorRepository, SanctionsRepository, TreasuryRepository
e IngestionLog
sobre las tablas definidas en schema.sql.
"""

import json
from dataclasses import fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import asyncpg

from app.core.domain.errors import TreasuryNotInitializedError, VendorAlreadyExistsError, VendorNotFoundError
from app.core.domain.models import (
    CompanyRules,
    DecisionStatus,
    IngestionRecord,
    IngestionStatus,
    ProcessedInvoice,
    TreasuryStatus,
    Vendor,
)

SQL_DIR = Path(__file__).parent
APPROVED = (DecisionStatus.AUTO_APPROVED.value, DecisionStatus.HUMAN_APPROVED.value)
NOT_REJECTED = (
    DecisionStatus.AUTO_APPROVED.value,
    DecisionStatus.SCALED_TO_HUMAN.value,
    DecisionStatus.HUMAN_APPROVED.value,
)
# Un reclamo que sigue en PROCESSING después de esto se da por colgado (el proceso murió) y se puede retomar
INGESTION_STALE_SECONDS = 300
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
                source_chat_id, decision_status, audit_explanation, evaluations, processed_at, file_sha256)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
            RETURNING *
            """,
            invoice.invoice_number, invoice.vendor_name, invoice.vendor_tax_id, invoice.bank_account,
            invoice.original_amount, invoice.original_currency, invoice.fx_rate_applied, invoice.usd_amount,
            invoice.due_date, invoice.ocr_confidence_score, invoice.channel_source, invoice.source_chat_id,
            invoice.decision_status.value, invoice.audit_explanation, invoice.evaluations, invoice.processed_at,
            invoice.file_sha256,
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

    async def find_by_file_hash(self, file_sha256: str, within_days: int) -> Optional[ProcessedInvoice]:
        since = datetime.utcnow() - timedelta(days=within_days)
        row = await self.db.require_pool().fetchrow(
            """
            SELECT * FROM invoices
            WHERE file_sha256 = $1 AND processed_at >= $2 AND decision_status = ANY($3::text[])
            ORDER BY processed_at DESC, id DESC LIMIT 1
            """,
            file_sha256, since, list(NOT_REJECTED),
        )
        return _row_to_invoice(row) if row else None


class PostgresIngestionLog:
    """Registro de entregas por canal: el PRIMARY KEY (channel, external_id) hace atómico el reclamo."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def claim(self, channel: str, external_id: str) -> Optional[IngestionRecord]:
        pool = self.db.require_pool()
        # Gana quien inserta, o quien retoma un reclamo colgado; el resto lee el registro existente
        won = await pool.fetchval(
            """
            INSERT INTO ingested_messages (channel, external_id) VALUES ($1, $2)
            ON CONFLICT (channel, external_id) DO UPDATE SET received_at = LOCALTIMESTAMP
            WHERE ingested_messages.status = $3
              AND ingested_messages.received_at < LOCALTIMESTAMP - make_interval(secs => $4)
            RETURNING TRUE
            """,
            channel, external_id, IngestionStatus.PROCESSING.value, INGESTION_STALE_SECONDS,
        )
        if won:
            return None
        row = await pool.fetchrow(
            "SELECT status, invoice_id FROM ingested_messages WHERE channel = $1 AND external_id = $2",
            channel, external_id,
        )
        # Si el ganador liberó el reclamo entre las dos consultas, se informa en proceso y el cliente reintenta
        if row is None:
            return IngestionRecord(status=IngestionStatus.PROCESSING)
        return IngestionRecord(status=IngestionStatus(row["status"]), invoice_id=row["invoice_id"])

    async def complete(self, channel: str, external_id: str, invoice_id: int) -> None:
        await self.db.require_pool().execute(
            "UPDATE ingested_messages SET status = $3, invoice_id = $4 WHERE channel = $1 AND external_id = $2",
            channel, external_id, IngestionStatus.COMPLETED.value, invoice_id,
        )

    async def release(self, channel: str, external_id: str) -> None:
        await self.db.require_pool().execute(
            "DELETE FROM ingested_messages WHERE channel = $1 AND external_id = $2 AND status = $3",
            channel, external_id, IngestionStatus.PROCESSING.value,
        )


class PostgresRulesRepository:
    """Repositorio de reglas corporativas."""

    def __init__(self, db: PostgresDatabase, defaults: CompanyRules):
        self.db = db
        self.defaults = defaults

    async def get(self, company_id: str) -> CompanyRules:
        row = await self.db.require_pool().fetchrow(
            """SELECT company_id, max_autonomous_usd, sarlaft_check_enabled, duplicate_check_days,
                      min_treasury_buffer_usd, max_payment_usd FROM company_rules WHERE company_id = $1""",
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
            max_payment_usd=float(row["max_payment_usd"]),
        )

    async def save(self, rules: CompanyRules) -> CompanyRules:
        await self.db.require_pool().execute(
            """
            INSERT INTO company_rules (company_id, max_autonomous_usd, sarlaft_check_enabled,
                duplicate_check_days, min_treasury_buffer_usd, max_payment_usd)
            VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT (company_id) DO UPDATE SET max_autonomous_usd = EXCLUDED.max_autonomous_usd,
                sarlaft_check_enabled = EXCLUDED.sarlaft_check_enabled,
                duplicate_check_days = EXCLUDED.duplicate_check_days,
                min_treasury_buffer_usd = EXCLUDED.min_treasury_buffer_usd,
                max_payment_usd = EXCLUDED.max_payment_usd
            """,
            rules.company_id, rules.max_autonomous_usd, rules.sarlaft_check_enabled,
            rules.duplicate_check_days, rules.min_treasury_buffer_usd, rules.max_payment_usd,
        )
        return rules


class PostgresVendorRepository:
    """Registro de proveedores verificados."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def find(self, tax_id: Optional[str], name: Optional[str]) -> Optional[Vendor]:
        # Llave normalizada (vendor_key en schema.sql): el OCR no siempre respeta puntos, guiones ni tildes.
        # El NIT manda; la razón social solo empata si su llave no queda vacía.
        row = await self.db.require_pool().fetchrow(
            """SELECT * FROM vendors
               WHERE vendor_key(tax_id) = vendor_key($1)
                  OR (vendor_key($2) <> '' AND vendor_key(legal_name) = vendor_key($2))
               ORDER BY (vendor_key(tax_id) = vendor_key($1)) DESC NULLS LAST LIMIT 1""",
            tax_id, name,
        )
        return _vendor(row) if row else None

    async def list_all(self) -> List[Vendor]:
        rows = await self.db.require_pool().fetch("SELECT * FROM vendors ORDER BY lower(legal_name)")
        return [_vendor(row) for row in rows]

    async def get(self, vendor_id: int) -> Optional[Vendor]:
        row = await self.db.require_pool().fetchrow("SELECT * FROM vendors WHERE id = $1", vendor_id)
        return _vendor(row) if row else None

    async def create(self, vendor: Vendor) -> Vendor:
        try:
            row = await self.db.require_pool().fetchrow(
                """INSERT INTO vendors (tax_id, legal_name, bank_account, is_pep, contract_amount_usd, active,
                                      updated_by, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *""",
                vendor.tax_id, vendor.legal_name, vendor.bank_account, vendor.is_pep, vendor.contract_amount_usd,
                vendor.active, vendor.updated_by, vendor.updated_at,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate(exc, vendor) from exc
        return _vendor(row)

    async def update(self, vendor: Vendor) -> Vendor:
        # tax_id e is_pep no se editan (D7): no están en el SET
        try:
            row = await self.db.require_pool().fetchrow(
                """UPDATE vendors SET legal_name = $2, bank_account = $3, contract_amount_usd = $4, active = $5,
                                      updated_by = $6, updated_at = $7
                   WHERE id = $1 RETURNING *""",
                vendor.id, vendor.legal_name, vendor.bank_account, vendor.contract_amount_usd, vendor.active,
                vendor.updated_by, vendor.updated_at,
            )
        except asyncpg.UniqueViolationError as exc:
            raise _duplicate(exc, vendor) from exc
        if row is None:
            raise VendorNotFoundError(vendor.id)
        return _vendor(row)


def _vendor(row) -> Vendor:
    contract = row["contract_amount_usd"]
    return Vendor(
        tax_id=row["tax_id"], legal_name=row["legal_name"], bank_account=row["bank_account"],
        is_pep=row["is_pep"], contract_amount_usd=float(contract) if contract is not None else None,
        active=row["active"] is not False, id=row["id"], updated_by=row["updated_by"], updated_at=row["updated_at"],
    )


def _duplicate(exc: asyncpg.UniqueViolationError, vendor: Vendor) -> VendorAlreadyExistsError:
    # vendors_tax_id_key y uq_vendors_tax_id_key son del NIT; uq_vendors_legal_name_key, de la razón social
    if exc.constraint_name == "uq_vendors_legal_name_key":
        return VendorAlreadyExistsError("legal_name", vendor.legal_name)
    return VendorAlreadyExistsError("tax_id", vendor.tax_id)


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
        # Las fechas se guardan en UTC sin zona: el mes en curso se corta en UTC.
        # Fecha de aprobación: processed_at en AUTO_APPROVED, decided_at en HUMAN_APPROVED (processed_at si falta,
        # como en el historial del seed). Comprometido = aprobado después de la foto del saldo (updated_at).
        # invoices no tiene company_id (MVP de una empresa): los acumulados son de toda la tabla.
        row = await self.db.require_pool().fetchrow(
            """
            WITH approved AS (
                SELECT usd_amount,
                       CASE WHEN decision_status = $2 THEN processed_at
                            ELSE COALESCE(decided_at, processed_at) END AS approved_at
                FROM invoices WHERE decision_status = ANY($3::text[])
            )
            SELECT t.balance_usd, t.monthly_budget_usd, t.updated_at,
                   (SELECT COALESCE(SUM(usd_amount), 0) FROM approved
                     WHERE approved_at >= date_trunc('month', timezone('UTC', now()))) AS month_spent_usd,
                   (SELECT COALESCE(SUM(usd_amount), 0) FROM approved
                     WHERE approved_at > t.updated_at) AS committed_usd
            FROM (SELECT 1) AS one
            LEFT JOIN treasury_accounts t ON t.company_id = $1
            """,
            company_id, DecisionStatus.AUTO_APPROVED.value, list(APPROVED),
        )
        month_spent = float(row["month_spent_usd"])
        if row["balance_usd"] is None:
            return TreasuryStatus(self.defaults.balance_usd, self.defaults.monthly_budget_usd, month_spent)
        return TreasuryStatus(
            balance_usd=float(row["balance_usd"]),
            monthly_budget_usd=float(row["monthly_budget_usd"]),
            month_spent_usd=month_spent,
            committed_usd=float(row["committed_usd"]),
            snapshot_at=row["updated_at"],
        )

    async def set_balance(
        self, company_id: str, balance_usd: float, as_of: datetime, monthly_budget_usd: Optional[float] = None
    ) -> TreasuryStatus:
        # Foto nueva: as_of (UTC, reloj de la app) deja fuera de lo comprometido todo lo aprobado hasta ahora.
        # Sin presupuesto en la solicitud, la fila existente conserva el suyo.
        await self.db.require_pool().execute(
            """INSERT INTO treasury_accounts (company_id, balance_usd, monthly_budget_usd, updated_at)
               VALUES ($1, $2, COALESCE($3::numeric, $4::numeric), $5)
               ON CONFLICT (company_id) DO UPDATE SET
                   balance_usd = EXCLUDED.balance_usd, updated_at = EXCLUDED.updated_at,
                   monthly_budget_usd = COALESCE($3::numeric, treasury_accounts.monthly_budget_usd)""",
            company_id, balance_usd, monthly_budget_usd, self.defaults.monthly_budget_usd, as_of,
        )
        return await self.get(company_id)

    async def set_monthly_budget(self, company_id: str, monthly_budget_usd: float) -> TreasuryStatus:
        # Solo UPDATE: un upsert crearía un saldo inventado y una foto nueva que libera lo comprometido (F7.1).
        result = await self.db.require_pool().execute(
            "UPDATE treasury_accounts SET monthly_budget_usd = $2 WHERE company_id = $1",
            company_id, monthly_budget_usd,
        )
        if result == "UPDATE 0":
            raise TreasuryNotInitializedError(company_id)
        return await self.get(company_id)
