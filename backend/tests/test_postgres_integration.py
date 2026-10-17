"""
Prueba de integración contra PostgreSQL real con el seed de demostración (TC-01..TC-07 vía API REST).
Se ejecuta solo si TEST_DATABASE_URL apunta a una base desechable:
    TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/blinka_test pytest
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from scripts.casos_demo import CASOS, SALDO_DEMO_USD

from .fakes import FakeGenAIClient

FIXTURES = Path(__file__).parent / "fixtures"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL no configurado")


@pytest.fixture()
def client(monkeypatch):
    import asyncpg
    import asyncio
    from fastapi.testclient import TestClient

    async def reset():
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        await conn.execute("DROP TABLE IF EXISTS ingested_messages, invoices, vendors, sanctions_list, treasury_accounts, company_rules")
        await conn.close()

    asyncio.run(reset())
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("DB_AUTO_MIGRATE", "true")
    monkeypatch.setenv("DB_SEED_DEMO", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")  # nunca llamar a la API real desde pytest

    from app.config import get_settings
    from app.container import Container
    from app.main import app

    get_settings.cache_clear()
    app.state.container = Container(get_settings())
    with TestClient(app) as test_client:
        yield test_client


def post_invoice(client, **payload):
    response = client.post("/api/invoices", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_suite_against_seeded_database(client):
    assert client.get("/api/health").json()["database"] == "connected"
    assert len(client.get("/api/invoices").json()) == 5
    treasury = client.get("/api/treasury").json()
    assert treasury["balance_usd"] == 8500 and treasury["monthly_budget_usd"] == 25000
    # La foto del seed es posterior a su historial: nada comprometido (F6.1)
    assert treasury["committed_usd"] == 0 and treasury["available_usd"] == 8500
    # Del seed solo DS-1042 (hace 3 días, 1.200 USD) cae en el mes; las aprobadas de hace 35 a 50 días no cuentan
    assert treasury["month_spent_usd"] == (1200.0 if datetime.utcnow().day > 3 else 0.0)

    # Como humo_produccion.py: foto del saldo antes de TC-01
    assert client.patch("/api/treasury", json={"balance_usd": SALDO_DEMO_USD}).json()["committed_usd"] == 0
    resultados = {}
    for caso, estado, regla, payload in CASOS:
        invoice = post_invoice(client, **payload)
        assert invoice["decision_status"] == estado, (caso, invoice["audit_explanation"])
        assert regla is None or regla in invoice["audit_explanation"], (caso, invoice["audit_explanation"])
        resultados[caso] = invoice
    tc04 = resultados["TC-04"]

    gbp = post_invoice(client, invoice_number="AWS-GBP-1", vendor_name="Amazon Web Services LATAM",
                       vendor_tax_id="US-91-1646860", original_amount=1000, original_currency="GBP")
    assert gbp["decision_status"] == "SCALED_TO_HUMAN" and "INTEG-04" in gbp["audit_explanation"]
    assert gbp["usd_amount"] == 0.0 and gbp["fx_rate_applied"] is None
    # INTEG-04: aprobarla comprometería $0 por un monto desconocido (F6.3)
    blocked = client.post(f"/api/invoices/{gbp['id']}/decision", json={"decision": "APPROVE", "decided_by": "CFO"})
    assert blocked.status_code == 409 and "INTEG-04" in blocked.json()["detail"]

    decision = client.post(f"/api/invoices/{tc04['id']}/decision",
                           json={"decision": "APPROVE", "decided_by": "CFO Blinka", "note": "Contrato vigente"})
    assert decision.status_code == 200 and decision.json()["decision_status"] == "HUMAN_APPROVED"
    assert "Solvencia al aprobar: disponible $8,050.00 USD" in decision.json()["audit_explanation"]
    # FIN-02 suma lo aprobado del mes, autónomo o humano: TC-01 (450) + TC-04 aprobada por el CFO (3.500)
    after = client.get("/api/treasury").json()
    assert after["month_spent_usd"] == treasury["month_spent_usd"] + 3950
    assert after["committed_usd"] == 3950 and after["available_usd"] == 8500 - 3950
    # Una foto nueva del saldo libera lo comprometido, sin tocar el gasto del mes
    snapshot = client.patch("/api/treasury", json={"balance_usd": 8500}).json()
    assert snapshot["committed_usd"] == 0 and snapshot["month_spent_usd"] == after["month_spent_usd"]
    assert snapshot["snapshot_at"] > treasury["snapshot_at"]
    assert client.post(f"/api/invoices/{tc04['id']}/decision",
                       json={"decision": "REJECT", "decided_by": "CFO"}).status_code == 409
    assert client.post("/api/invoices/9999/decision", json={"decision": "REJECT", "decided_by": "CFO"}).status_code == 404

    rules = client.post("/api/rules", json={"max_autonomous_usd": 5000}).json()
    assert rules["max_autonomous_usd"] == 5000 and client.get("/api/rules").json()["max_autonomous_usd"] == 5000
    # F7.2: la columna nueva toma el default en la fila del seed y se guarda; nunca bajo el umbral
    assert rules["max_payment_usd"] == 20000
    assert client.post("/api/rules", json={"max_payment_usd": 4000}).status_code == 422
    assert client.post("/api/rules", json={"max_payment_usd": 30000}).json()["max_payment_usd"] == 30000
    assert client.get("/api/rules").json()["max_payment_usd"] == 30000

    upload = client.post("/api/invoices/upload", files={"file": ("f.png", b"\x89PNG fake", "image/png")})
    assert upload.status_code == 201 and upload.json()["decision_status"] == "SCALED_TO_HUMAN"
    assert upload.json()["channel_source"] == "WEB"
    assert client.post("/api/invoices/upload", files={"file": ("f.txt", b"x", "text/plain")}).status_code == 415


def gemini_reads(invoice_number, vendor_name, tax_id, bank_account, amount, currency, due_date):
    """Respuesta simulada de Gemini con lo que se lee en el fixture (ver tests/fixtures/README.md)."""
    return json.dumps({"invoice_number": invoice_number, "vendor_name": vendor_name, "vendor_tax_id": tax_id,
                       "bank_account": bank_account, "amount": amount, "currency": currency,
                       "due_date": due_date, "confidence": 0.98})


def test_upload_de_fixtures_produce_la_decision_esperada_con_el_seed(client):
    """F1.7: subida real por la API + PostgreSQL con seed; solo el cliente de Gemini es simulado."""
    from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter

    cases = [
        ("factura_devstudio.png", "image/png",
         gemini_reads("DS-2026-1107", "DevStudio LatAm S.A.S.", "900.584.112-4", "CO-BANCOLOMBIA-11122233344",
                      4200000.0, "COP", "2026-11-30"),
         "AUTO_APPROVED", None),
        ("factura_nube_andina.pdf", "application/pdf",
         gemini_reads("NA-4521", "Nube Andina Consultores S.A.S.", "901.223.450-1", "CO-DAVIVIENDA-55566677788",
                      12600000.0, "COP", "2026-12-05"),
         "SCALED_TO_HUMAN", "HITL-01"),
        ("factura_global_trade.png", "image/png",
         gemini_reads("GTP-0091", "Global Trade Partners Ltd", "PA-155-7788", "PA-BANCO-PACIFICO-998877",
                      900.0, "USD", "2026-11-20"),
         "REJECTED", "COMP-01"),
    ]
    process_invoice = client.app.state.container.process_invoice
    for fixture, mime_type, gemini_json, expected_status, expected_code in cases:
        process_invoice.ocr = GeminiOCRAdapter("test-key", "gemini-test", client=FakeGenAIClient(text=gemini_json))
        with open(FIXTURES / fixture, "rb") as file:
            response = client.post("/api/invoices/upload", files={"file": (fixture, file, mime_type)})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["decision_status"] == expected_status, (fixture, body["audit_explanation"])
        if expected_code:
            assert expected_code in body["audit_explanation"]
        assert body["channel_source"] == "WEB"

    stored = {inv["invoice_number"]: inv["decision_status"] for inv in client.get("/api/invoices").json()}
    assert stored["DS-2026-1107"] == "AUTO_APPROVED" and stored["GTP-0091"] == "REJECTED"


def run_with_db(scenario):
    """Corre un escenario async contra una base recién migrada (sin seed)."""
    import asyncio
    import asyncpg
    from app.adapters.outbound.db.postgres_repository import PostgresDatabase

    async def main():
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        await conn.execute("DROP TABLE IF EXISTS ingested_messages, invoices, vendors, sanctions_list, treasury_accounts, company_rules")
        await conn.close()
        db = PostgresDatabase(TEST_DATABASE_URL)
        await db.connect(auto_migrate=True)
        try:
            await scenario(db)
        finally:
            await db.close()

    asyncio.run(main())


def test_ingestion_log_reclamo_atomico_completar_liberar_y_retomar():
    import asyncio
    from app.adapters.outbound.db.postgres_repository import PostgresIngestionLog, PostgresInvoiceRepository
    from app.core.domain.models import DecisionStatus, IngestionStatus, ProcessedInvoice

    async def scenario(db):
        log = PostgresIngestionLog(db)
        # Reclamos simultáneos desde conexiones distintas del pool: solo uno gana
        results = await asyncio.gather(*[log.claim("WEB", "key-1") for _ in range(5)])
        assert results.count(None) == 1
        assert all(r.status == IngestionStatus.PROCESSING and r.invoice_id is None for r in results if r)

        # Liberar en proceso permite reintentar
        await log.release("WEB", "key-1")
        assert await log.claim("WEB", "key-1") is None

        invoice = await PostgresInvoiceRepository(db).save(ProcessedInvoice(
            invoice_number="X-1", vendor_name="Proveedor", original_amount=10, original_currency="USD",
            usd_amount=10, fx_rate_applied=1.0, decision_status=DecisionStatus.AUTO_APPROVED,
            audit_explanation="ok"))
        await log.complete("WEB", "key-1", invoice.id)
        await log.release("WEB", "key-1")  # una entrega completada no se libera
        record = await log.claim("WEB", "key-1")
        assert record.status == IngestionStatus.COMPLETED and record.invoice_id == invoice.id

        # La misma clave en otro canal es otra entrega
        assert await log.claim("API", "key-1") is None

        # Un reclamo colgado más de INGESTION_STALE_SECONDS se puede retomar; uno completado nunca
        await db.require_pool().execute(
            "UPDATE ingested_messages SET received_at = LOCALTIMESTAMP - interval '10 minutes'")
        assert await log.claim("API", "key-1") is None
        assert (await log.claim("WEB", "key-1")).status == IngestionStatus.COMPLETED

    run_with_db(scenario)


def test_find_by_file_hash_respeta_ventana_y_estados():
    from datetime import datetime, timedelta
    from app.adapters.outbound.db.postgres_repository import PostgresInvoiceRepository
    from app.core.domain.models import DecisionStatus, ProcessedInvoice

    def invoice(number, status, sha, days_ago=0):
        return ProcessedInvoice(
            invoice_number=number, vendor_name="Proveedor", original_amount=10, original_currency="USD",
            usd_amount=10, fx_rate_applied=1.0, decision_status=status, audit_explanation="x",
            file_sha256=sha, processed_at=datetime.utcnow() - timedelta(days=days_ago))

    async def scenario(db):
        repo = PostgresInvoiceRepository(db)
        ok = await repo.save(invoice("A", DecisionStatus.SCALED_TO_HUMAN, "a" * 64))
        assert ok.file_sha256 == "a" * 64
        await repo.save(invoice("B", DecisionStatus.REJECTED, "b" * 64))
        await repo.save(invoice("C", DecisionStatus.AUTO_APPROVED, "c" * 64, days_ago=40))

        found = await repo.find_by_file_hash("a" * 64, 30)
        assert found.id == ok.id and found.invoice_number == "A"
        assert await repo.find_by_file_hash("b" * 64, 30) is None  # rechazada
        assert await repo.find_by_file_hash("c" * 64, 30) is None  # fuera de la ventana
        assert await repo.find_by_file_hash("d" * 64, 30) is None

    run_with_db(scenario)


def test_ingesta_idempotente_de_punta_a_punta_con_el_seed(client):
    """F2.7: Idempotency-Key repetida, solicitudes concurrentes y el mismo archivo con otra clave, sobre PostgreSQL."""
    import asyncio
    import asyncpg
    from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter

    process_invoice = client.app.state.container.process_invoice
    process_invoice.ocr = GeminiOCRAdapter("test-key", "gemini-test", client=FakeGenAIClient(text=gemini_reads(
        "NA-4521", "Nube Andina Consultores S.A.S.", "901.223.450-1", "CO-DAVIVIENDA-55566677788",
        12600000.0, "COP", "2026-12-05")))
    fixture = (FIXTURES / "factura_nube_andina.pdf").read_bytes()

    def upload(key):
        return client.post("/api/invoices/upload", headers={"Idempotency-Key": key},
                           files={"file": ("f.pdf", fixture, "application/pdf")})

    first, again = upload("web-1"), upload("web-1")
    assert first.status_code == 201 and again.status_code == 200
    assert again.json()["id"] == first.json()["id"] and first.json()["decision_status"] == "SCALED_TO_HUMAN"

    copy = upload("web-2")  # mismo archivo, otra entrega: INTEG-01 por hash, sin volver a llamar al OCR
    assert copy.status_code == 201 and copy.json()["decision_status"] == "REJECTED"
    assert f"#{first.json()['id']}" in copy.json()["audit_explanation"]
    assert len(process_invoice.ocr.client.calls) == 1

    async def check_db_and_race():
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        try:
            rows = await conn.fetch("SELECT external_id, status, invoice_id FROM ingested_messages ORDER BY external_id")
            assert [(r["external_id"], r["status"]) for r in rows] == [("web-1", "COMPLETED"), ("web-2", "COMPLETED")]
            assert rows[0]["invoice_id"] == first.json()["id"]
            hashes = await conn.fetchval("SELECT COUNT(DISTINCT file_sha256) FROM invoices WHERE file_sha256 IS NOT NULL")
            assert hashes == 1
        finally:
            await conn.close()

    asyncio.run(check_db_and_race())


def test_solicitudes_concurrentes_con_la_misma_clave_procesan_una_sola_vez_en_postgres():
    """F2.7: varias solicitudes simultáneas con la misma clave sobre PostgreSQL real: una factura y un aviso."""
    import asyncio
    from app.adapters.outbound.db.postgres_repository import (
        PostgresIngestionLog, PostgresInvoiceRepository, PostgresSanctionsRepository, PostgresVendorRepository,
    )
    from app.core.domain.models import ExtractedInvoice
    from app.core.domain.rules_pipeline import RulesPipeline
    from app.core.use_cases import ProcessInvoiceUseCase

    from .fakes import FakeOCR, FakeRates, FixedTreasury, InMemoryRules, SpyNotifier

    async def scenario(db):
        notifier = SpyNotifier()
        use_case = ProcessInvoiceUseCase(
            ocr=FakeOCR(ExtractedInvoice(invoice_number="R-1", vendor_name="Proveedor Nuevo", original_amount=100)),
            fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=PostgresInvoiceRepository(db),
            rules=InMemoryRules(), vendors=PostgresVendorRepository(db), sanctions=PostgresSanctionsRepository(db),
            treasury=FixedTreasury(), company_id="TEST", notifier=notifier, ingestion=PostgresIngestionLog(db),
        )
        results = await asyncio.gather(*[
            use_case.from_document(b"misma factura", "image/png", "WEB", external_id="race-1") for _ in range(4)
        ])
        assert sum(not r.duplicate for r in results) == 1
        assert len(notifier.decisions) == 1 and len(notifier.received) == 1
        assert await db.require_pool().fetchval("SELECT COUNT(*) FROM invoices") == 1

        again = await use_case.from_document(b"misma factura", "image/png", "WEB", external_id="race-1")
        assert again.duplicate and again.invoice.invoice_number == "R-1"

    run_with_db(scenario)


def test_tesoreria_compromete_lo_aprobado_despues_de_la_foto_con_la_fecha_de_aprobacion():
    """F6.1: comprometido y gasto del mes usan processed_at en AUTO_APPROVED y decided_at en HUMAN_APPROVED;
    la foto del saldo se escribe en UTC."""
    from datetime import datetime, timedelta
    from app.adapters.outbound.db.postgres_repository import PostgresInvoiceRepository, PostgresTreasuryRepository
    from app.core.domain.models import DecisionStatus, ProcessedInvoice, TreasuryStatus

    def invoice(number, amount, status, processed_at):
        return ProcessedInvoice(
            invoice_number=number, vendor_name="Proveedor", original_amount=amount, original_currency="USD",
            usd_amount=amount, fx_rate_applied=1.0, decision_status=status, audit_explanation="x",
            processed_at=processed_at)

    async def scenario(db):
        invoices = PostgresInvoiceRepository(db)
        treasury = PostgresTreasuryRepository(db, TreasuryStatus(balance_usd=0.0, monthly_budget_usd=0.0))
        now = datetime.utcnow()

        async def approve(saved, decided_at):
            await invoices.update_decision(saved.id, DecisionStatus.HUMAN_APPROVED, "x", "CFO", decided_at, None,
                                           expected_status=DecisionStatus.SCALED_TO_HUMAN)

        # Aprobada antes de la foto: cuenta en el mes, no compromete
        await invoices.save(invoice("A", 100, DecisionStatus.AUTO_APPROVED, now - timedelta(minutes=2)))
        photo = await treasury.set_balance("BLINKA_DEFAULT", 8500, datetime.utcnow())
        assert photo.committed_usd == 0 and photo.balance_usd == 8500
        # Sin foto previa, el DEFAULT del esquema también queda en UTC aunque la base esté en otra zona
        async with db.require_pool().acquire() as conn:
            await conn.execute("INSERT INTO treasury_accounts (company_id, balance_usd, monthly_budget_usd) "
                               "VALUES ('OTRA', 1, 1)")
            default_at = await conn.fetchval("SELECT updated_at FROM treasury_accounts WHERE company_id = 'OTRA'")
        assert abs((default_at - datetime.utcnow()).total_seconds()) < 60

        await invoices.save(invoice("B", 200, DecisionStatus.AUTO_APPROVED, datetime.utcnow()))
        await approve(await invoices.save(invoice("C", 300, DecisionStatus.SCALED_TO_HUMAN, datetime.utcnow())),
                      datetime.utcnow())
        # Ingresada hace 40 días y aprobada hoy: compromete y cuenta en el mes por decided_at
        await approve(await invoices.save(invoice("D", 400, DecisionStatus.SCALED_TO_HUMAN, now - timedelta(days=40))),
                      datetime.utcnow())
        # Ingresada hoy y aprobada hace 40 días: no compromete ni cuenta en el mes
        await approve(await invoices.save(invoice("E", 500, DecisionStatus.SCALED_TO_HUMAN, datetime.utcnow())),
                      now - timedelta(days=40))
        # Escaladas y rechazadas no cuentan
        await invoices.save(invoice("F", 600, DecisionStatus.SCALED_TO_HUMAN, datetime.utcnow()))
        await invoices.save(invoice("G", 700, DecisionStatus.REJECTED, datetime.utcnow()))

        status = await treasury.get("BLINKA_DEFAULT")
        assert status.committed_usd == 900 and status.available_usd == 7600
        assert status.month_spent_usd == 1000

        fresh = await treasury.set_balance("BLINKA_DEFAULT", 9000, datetime.utcnow())
        assert fresh.balance_usd == 9000 and fresh.committed_usd == 0 and fresh.month_spent_usd == 1000
        assert fresh.snapshot_at > photo.snapshot_at

    run_with_db(scenario)


def test_presupuesto_solo_update_sin_mover_la_foto_ni_crear_la_fila():
    """F7.1: set_monthly_budget nunca inserta (un upsert inventaría saldo y foto) y no mueve updated_at;
    set_balance conserva el presupuesto guardado si no llega uno nuevo."""
    from datetime import datetime, timedelta
    import pytest as _pytest
    from app.adapters.outbound.db.postgres_repository import PostgresTreasuryRepository
    from app.core.domain.errors import TreasuryNotInitializedError
    from app.core.domain.models import TreasuryStatus

    async def scenario(db):
        treasury = PostgresTreasuryRepository(db, TreasuryStatus(balance_usd=0.0, monthly_budget_usd=0.0))
        pool = db.require_pool()

        with _pytest.raises(TreasuryNotInitializedError):
            await treasury.set_monthly_budget("EMPRESA", 12000)
        assert await pool.fetchval("SELECT count(*) FROM treasury_accounts WHERE company_id = 'EMPRESA'") == 0

        foto = datetime.utcnow().replace(microsecond=0) - timedelta(hours=1)
        creada = await treasury.set_balance("EMPRESA", 8500, foto, monthly_budget_usd=25000)
        assert (creada.balance_usd, creada.monthly_budget_usd, creada.snapshot_at) == (8500, 25000, foto)

        cambiada = await treasury.set_monthly_budget("EMPRESA", 12000)
        assert (cambiada.balance_usd, cambiada.monthly_budget_usd, cambiada.snapshot_at) == (8500, 12000, foto)

        nueva_foto = foto + timedelta(minutes=30)
        sin_presupuesto = await treasury.set_balance("EMPRESA", 9000, nueva_foto)
        assert (sin_presupuesto.balance_usd, sin_presupuesto.monthly_budget_usd) == (9000, 12000)
        assert sin_presupuesto.snapshot_at == nueva_foto

    run_with_db(scenario)


def test_lista_permitida_con_el_seed_alta_unicidad_y_baja_logica(client):
    """F7.3: la migración deja activos a los proveedores del seed; NIT y razón social (sin mayúsculas) son únicos;
    la baja es lógica y find la sigue devolviendo para COMP-02/INTEG-02."""
    vendors = client.get("/api/vendors").json()
    assert len(vendors) == 6 and all(v["active"] for v in vendors)
    aws = next(v for v in vendors if v["tax_id"] == "US-91-1646860")

    new = {"tax_id": "901.555.010-2", "legal_name": "Diseño Creativo Bogotá S.A.S.",
           "bank_account": "CO-BANCOLOMBIA-55500011122", "updated_by": "CFO Demo"}
    created = client.post("/api/vendors", json=new)
    assert created.status_code == 201 and created.json()["updated_at"].endswith("Z")
    assert client.post("/api/vendors", json={**new, "legal_name": "Otro"}).status_code == 409          # NIT
    assert client.post("/api/vendors", json={**new, "tax_id": "OTRO",
                                             "legal_name": "DISEÑO CREATIVO bogotá s.a.s."}).status_code == 409
    assert client.patch(f"/api/vendors/{aws['id']}",
                        json={"legal_name": new["legal_name"].lower(), "updated_by": "CFO"}).status_code == 409
    assert client.patch("/api/vendors/99999", json={"active": False, "updated_by": "CFO"}).status_code == 404

    off = client.patch(f"/api/vendors/{aws['id']}", json={"active": False, "updated_by": "CFO Demo"}).json()
    assert off["active"] is False and off["updated_by"] == "CFO Demo" and off["contract_amount_usd"] == 1000
    assert len(client.get("/api/vendors").json()) == 7

    async def find_inactive():
        import asyncpg
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        row = await conn.fetchrow("SELECT active, updated_at FROM vendors WHERE tax_id = 'US-91-1646860'")
        await conn.close()
        return row

    import asyncio
    row = asyncio.run(find_inactive())
    assert row["active"] is False
    assert abs((row["updated_at"] - datetime.utcnow()).total_seconds()) < 60  # UTC, aunque la base esté en Bogotá

    async def find_with_repository():
        # Pool propio: el de la app vive en el event loop del TestClient
        from app.adapters.outbound.db.postgres_repository import PostgresDatabase, PostgresVendorRepository
        db = PostgresDatabase(TEST_DATABASE_URL)
        await db.connect(auto_migrate=False)
        try:
            return await PostgresVendorRepository(db).find("US-91-1646860", None)
        finally:
            await db.close()

    found = asyncio.run(find_with_repository())
    assert found.active is False and found.bank_account == "US-CHASE-000123456"


def test_vendor_key_de_postgres_coincide_con_normalize_y_find_tolera_formatos(client):
    """F7.3: find() y la unicidad usan vendor_key (schema.sql), la misma llave que _normalize del Core.
    Los formatos son los que el OCR puede devolver para proveedores del seed."""
    import asyncio
    import asyncpg
    from app.adapters.outbound.db.postgres_repository import PostgresDatabase, PostgresVendorRepository
    from app.core.domain.rules_pipeline import _normalize

    samples = ["900.584.112-4", "Logística Express MX S.A. de C.V.", "Diseño Creativo Bogotá S.A.S.",
               "  ÁÉÍÓÚ ñ Ü ç  ", "PA-155-7788", "...", ""]
    lookups = [
        ("900584112-4", None, "900.584.112-4"),
        ("lem850101ab1", None, "LEM850101AB1"),
        (None, "Logistica Express MX SA de CV", "LEM850101AB1"),   # sin tildes ni puntos
        (None, "NUBE ANDINA CONSULTORES SAS", "901.223.450-1"),
        ("US-91-1646860", "Nube Andina Consultores S.A.S.", "US-91-1646860"),  # el NIT manda sobre el nombre
        (None, "...", None),
        (None, None, None),
    ]

    async def scenario():
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        keys = [await conn.fetchval("SELECT vendor_key($1)", s) for s in samples]
        await conn.close()
        db = PostgresDatabase(TEST_DATABASE_URL)
        await db.connect(auto_migrate=False)
        try:
            repo = PostgresVendorRepository(db)
            found = [await repo.find(tax_id, name) for tax_id, name, _ in lookups]
        finally:
            await db.close()
        return keys, found

    keys, found = asyncio.run(scenario())
    assert keys == [_normalize(s) for s in samples]
    assert [f.tax_id if f else None for f in found] == [expected for *_, expected in lookups]

    new = {"tax_id": "9005841124", "legal_name": "Otro S.A.S.", "bank_account": "X", "updated_by": "CFO"}
    assert client.post("/api/vendors", json=new).status_code == 409                       # NIT de DevStudio
    assert client.post("/api/vendors", json={**new, "tax_id": "NUEVO-1",
                                             "legal_name": "Devstudio Latam SAS"}).status_code == 409


def test_find_match_de_sanciones_tolera_el_formato_del_ocr(client):
    """COMP-01 compara con vendor_key: el NIT, la razón social o la cuenta sancionados empatan aunque el OCR
    los lea sin guiones, puntos ni mayúsculas. Una llave vacía (nombre vacío o solo símbolos) no empata."""
    import asyncio
    from app.adapters.outbound.db.postgres_repository import PostgresDatabase, PostgresSanctionsRepository

    lookups = [
        (None, "PA1557788", None),
        ("global trade partners ltd.", None, None),
        (None, None, "PA BANCO PACIFICO 998877"),
        ("", None, None),
        ("...", "--", " - "),
        (None, None, None),
    ]

    async def scenario():
        db = PostgresDatabase(TEST_DATABASE_URL)
        await db.connect(auto_migrate=False)
        try:
            repo = PostgresSanctionsRepository(db)
            return [await repo.find_match(*lookup) for lookup in lookups]
        finally:
            await db.close()

    matches = asyncio.run(scenario())
    assert matches == ["OFAC: Global Trade Partners Ltd"] * 3 + [None] * 3
