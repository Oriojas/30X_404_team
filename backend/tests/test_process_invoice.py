"""
Pruebas de los casos de uso ProcessInvoice y DecideInvoice con adaptadores falsos.
Demuestran que el Core funciona sin Gemini, PostgreSQL ni Telegram.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.core.domain.errors import InvalidDecisionStateError, InvoiceNotFoundError, UnconvertedAmountApprovalError
from app.core.domain.models import DecisionStatus, ExtractedInvoice, HumanDecision, ProcessedInvoice, Vendor
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import DecideInvoiceUseCase, ProcessInvoiceUseCase

from .fakes import (
    FakeOCR, FakeRates, FixedTreasury, InMemoryInvoices, InMemoryRules, InMemoryVendors, LedgerTreasury, NoSanctions,
    SpyNotifier,
)

VENDOR = Vendor("900.584.112-4", "DevStudio LatAm S.A.S.", contract_amount_usd=5000)


def build(extracted):
    invoices, notifier = InMemoryInvoices(), SpyNotifier()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(extracted), fx_rates=FakeRates(), pipeline=RulesPipeline(),
        invoices=invoices, rules=InMemoryRules(), vendors=InMemoryVendors(VENDOR), sanctions=NoSanctions(),
        treasury=FixedTreasury(), company_id="TEST", notifier=notifier,
    )
    return use_case, invoices, notifier


def decider(invoices, notifier=None, treasury=None):
    return DecideInvoiceUseCase(invoices, treasury or FixedTreasury(), InMemoryRules(), "TEST", notifier)


def cop_invoice(number="DS-1", amount=1_500_000):
    return ExtractedInvoice(invoice_number=number, vendor_name=VENDOR.legal_name,
                            original_amount=amount, original_currency="COP")


def test_new_vendor_is_scaled_then_known_vendor_is_approved_and_duplicate_rejected():
    use_case, invoices, notifier = build(cop_invoice())

    first = asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=42)).invoice
    assert first.usd_amount == 357.14 and first.fx_rate_applied == 4200.0
    assert first.decision_status == DecisionStatus.SCALED_TO_HUMAN  # HITL-02: sin historial
    assert notifier.received == [("TELEGRAM", 42)]
    assert notifier.decisions[-1].source_chat_id == 42

    decide = decider(invoices, notifier)
    approved = asyncio.run(decide.execute(first.id, HumanDecision.APPROVE, "CFO Blinka", "Proveedor validado"))
    assert approved.decision_status == DecisionStatus.HUMAN_APPROVED
    assert approved.decided_by == "CFO Blinka" and "Proveedor validado" in approved.audit_explanation

    second = asyncio.run(use_case.from_extracted(cop_invoice("DS-2", 2_100_000), "API")).invoice
    assert second.decision_status == DecisionStatus.AUTO_APPROVED

    repeated = asyncio.run(use_case.from_extracted(cop_invoice("DS-2", 2_100_000), "API")).invoice
    assert repeated.decision_status == DecisionStatus.REJECTED
    assert "INTEG-01" in repeated.audit_explanation


def test_human_decision_only_applies_to_scaled_invoices():
    use_case, invoices, notifier = build(cop_invoice())
    decide = decider(invoices, notifier)

    with pytest.raises(InvoiceNotFoundError):
        asyncio.run(decide.execute(99, HumanDecision.APPROVE, "CFO"))

    scaled = asyncio.run(use_case.from_extracted(cop_invoice(), "API")).invoice
    rejected = asyncio.run(decide.execute(scaled.id, HumanDecision.REJECT, "CFO"))
    assert rejected.decision_status == DecisionStatus.HUMAN_REJECTED

    with pytest.raises(InvalidDecisionStateError):
        asyncio.run(decide.execute(scaled.id, HumanDecision.APPROVE, "CFO"))


def test_concurrent_human_decisions_only_one_wins():
    use_case, invoices, notifier = build(cop_invoice())
    scaled = asyncio.run(use_case.from_extracted(cop_invoice(), "API")).invoice
    decide = decider(invoices, notifier)

    async def race():
        return await asyncio.gather(
            decide.execute(scaled.id, HumanDecision.APPROVE, "CFO"),
            decide.execute(scaled.id, HumanDecision.REJECT, "Tesorero"),
            return_exceptions=True,
        )

    results = asyncio.run(race())
    assert sum(isinstance(r, InvalidDecisionStateError) for r in results) == 1
    assert invoices.items[scaled.id].decided_by in {"CFO", "Tesorero"}


def test_unknown_currency_is_never_converted_at_one_to_one():
    use_case, invoices, _ = build(ExtractedInvoice(invoice_number="DS-9", vendor_name=VENDOR.legal_name,
                                                   original_amount=1000, original_currency="GBP"))
    result = asyncio.run(use_case.from_document(b"pdf", "application/pdf", "WEB")).invoice
    assert result.decision_status == DecisionStatus.SCALED_TO_HUMAN
    assert "INTEG-04" in result.audit_explanation
    assert result.usd_amount == 0.0 and result.fx_rate_applied is None


def test_notification_router_only_reaches_the_origin_channel():
    from app.adapters.outbound.notifications.channel_router import ChannelNotificationRouter

    telegram = SpyNotifier()
    router = ChannelNotificationRouter({"TELEGRAM": telegram})
    use_case, _, _ = build(cop_invoice())
    use_case.notifier = router

    asyncio.run(use_case.from_document(b"img", "image/jpeg", "WEB"))
    assert telegram.received == [] and telegram.decisions == []

    asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=7))
    assert telegram.received == [("TELEGRAM", 7)] and len(telegram.decisions) == 1


def test_aprobar_revalida_la_solvencia_y_registra_la_excepcion():
    """TC-05: escalada por FIN-01; la persona puede aprobarla, y el Audit Log deja el disponible y la alerta."""
    big = Vendor("LEM850101AB1", "Logística Express MX S.A. de C.V.", contract_amount_usd=15000)
    invoices, notifier = InMemoryInvoices(), SpyNotifier()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(None), fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=invoices, rules=InMemoryRules(),
        vendors=InMemoryVendors(big), sanctions=NoSanctions(), treasury=FixedTreasury(), company_id="TEST",
        notifier=notifier,
    )
    tc05 = asyncio.run(use_case.from_extracted(ExtractedInvoice(
        invoice_number="LEM-3400", vendor_name=big.legal_name, original_amount=10000, original_currency="USD"), "API")).invoice
    assert tc05.decision_status == DecisionStatus.SCALED_TO_HUMAN and "FIN-01" in tc05.audit_explanation

    treasury = FixedTreasury(committed_usd=1500.0)
    approved = asyncio.run(decider(invoices, notifier, treasury).execute(tc05.id, HumanDecision.APPROVE, "CFO Blinka"))

    assert approved.decision_status == DecisionStatus.HUMAN_APPROVED
    tail = approved.audit_explanation.split(" | ")[-1]
    assert "disponible $7,000.00 USD" in tail and "Excepción aprobada por CFO Blinka" in tail and "[FIN-01]" in tail


def test_aprobar_sin_alertas_fin_lo_deja_dicho():
    use_case, invoices, notifier = build(cop_invoice())
    scaled = asyncio.run(use_case.from_extracted(cop_invoice(), "API")).invoice  # HITL-02, no FIN
    approved = asyncio.run(decider(invoices, notifier).execute(scaled.id, HumanDecision.APPROVE, "CFO"))
    assert "disponible $8,500.00 USD" in approved.audit_explanation and "sin alertas FIN" in approved.audit_explanation
    assert "Excepción" not in approved.audit_explanation


def test_factura_sin_conversion_a_usd_no_se_puede_aprobar_pero_si_rechazar():
    use_case, invoices, notifier = build(ExtractedInvoice(invoice_number="DS-9", vendor_name=VENDOR.legal_name,
                                                          original_amount=1000, original_currency="GBP"))
    integ04 = asyncio.run(use_case.from_document(b"pdf", "application/pdf", "WEB")).invoice
    assert integ04.usd_amount == 0 and "INTEG-04" in integ04.audit_explanation
    decide = decider(invoices, notifier)

    with pytest.raises(UnconvertedAmountApprovalError):
        asyncio.run(decide.execute(integ04.id, HumanDecision.APPROVE, "CFO"))
    assert invoices.items[integ04.id].decision_status == DecisionStatus.SCALED_TO_HUMAN

    rejected = asyncio.run(decide.execute(integ04.id, HumanDecision.REJECT, "CFO"))
    assert rejected.decision_status == DecisionStatus.HUMAN_REJECTED


def ledger_setup(lock):
    """Tesorería que compromete lo aprobado ($8,500, colchón $1,000) y un proveedor con historial anterior a la foto."""
    invoices = InMemoryInvoices()
    # Historial anterior a la foto: da antigüedad al proveedor (HITL-02) y no compromete
    invoices.items[1] = ProcessedInvoice(
        id=1, invoice_number="OLD-1", vendor_name=VENDOR.legal_name, original_amount=100, original_currency="USD",
        usd_amount=100, fx_rate_applied=1.0, decision_status=DecisionStatus.AUTO_APPROVED, audit_explanation="x",
        processed_at=datetime.utcnow() - timedelta(days=10))
    treasury = LedgerTreasury(invoices)
    rules = InMemoryRules(max_autonomous_usd=20000)
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(None), fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=invoices, rules=rules,
        vendors=InMemoryVendors(Vendor(VENDOR.tax_id, VENDOR.legal_name, contract_amount_usd=20000)),
        sanctions=NoSanctions(), treasury=treasury, company_id="TEST", solvency_lock=lock,
    )
    decide = DecideInvoiceUseCase(invoices, treasury, rules, "TEST", solvency_lock=lock)
    return use_case, decide, invoices, treasury


def usd(number, amount):
    return ExtractedInvoice(invoice_number=number, vendor_name=VENDOR.legal_name, original_amount=amount,
                            original_currency="USD")


def test_dos_ingestas_concurrentes_no_comprometen_mas_que_el_disponible():
    """F6.4: $8,500 de saldo y $1,000 de colchón; facturas de $4,000 y $4,100 a la vez: solo una sale aprobada sola.
    (Montos distintos para que INTEG-01 no las tome como duplicadas.)"""
    use_case, _, _, _ = ledger_setup(asyncio.Lock())

    async def race():
        return await asyncio.gather(use_case.from_extracted(usd("DS-A", 4000), "TELEGRAM"),
                                    use_case.from_extracted(usd("DS-B", 4100), "WEB"))

    first, second = (r.invoice for r in asyncio.run(race()))
    statuses = sorted([first.decision_status, second.decision_status])
    assert statuses == [DecisionStatus.AUTO_APPROVED, DecisionStatus.SCALED_TO_HUMAN]
    scaled = first if first.decision_status == DecisionStatus.SCALED_TO_HUMAN else second
    assert "FIN-03" in scaled.audit_explanation


def test_aprobacion_e_ingesta_simultaneas_comparten_el_candado():
    """F6.4: una aprobación y una ingesta a la vez leen el disponible en orden, no el mismo valor."""
    use_case, decide, _, _ = ledger_setup(asyncio.Lock())
    scaled = asyncio.run(use_case.from_extracted(usd("DS-BIG", 15000), "API")).invoice  # FIN-01: $15,000 > $8,500
    assert scaled.decision_status == DecisionStatus.SCALED_TO_HUMAN

    async def race():
        return await asyncio.gather(decide.execute(scaled.id, HumanDecision.APPROVE, "CFO"),
                                    use_case.from_extracted(usd("DS-C", 4000), "WEB"))

    approved, ingested = asyncio.run(race())
    assert approved.decision_status == DecisionStatus.HUMAN_APPROVED
    # La aprobación tomó el candado primero y comprometió $15,000: la ingesta ve el disponible ya negativo
    assert ingested.invoice.decision_status == DecisionStatus.SCALED_TO_HUMAN
    assert "FIN-01" in ingested.invoice.audit_explanation


def test_container_comparte_un_solo_candado_de_solvencia():
    """D7: ingesta, decisión humana y foto del saldo usan la misma instancia, cableada en container.py."""
    from app.config import Settings
    from app.container import Container

    container = Container(Settings(database_url=None, gemini_api_key="", telegram_bot_token=""))
    lock = container.process_invoice.solvency_lock
    assert container.decide_invoice.solvency_lock is lock and container.update_treasury.solvency_lock is lock

