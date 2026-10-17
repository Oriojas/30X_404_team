"""
Pruebas de los casos de uso ProcessInvoice y DecideInvoice con adaptadores falsos.
Demuestran que el Core funciona sin Gemini, PostgreSQL ni Telegram.
"""

import asyncio

import pytest

from app.core.domain.errors import InvalidDecisionStateError, InvoiceNotFoundError
from app.core.domain.models import DecisionStatus, ExtractedInvoice, HumanDecision, Vendor
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import DecideInvoiceUseCase, ProcessInvoiceUseCase

from .fakes import (
    FakeOCR, FakeRates, FixedTreasury, InMemoryInvoices, InMemoryRules, InMemoryVendors, NoSanctions, SpyNotifier,
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

    decide = DecideInvoiceUseCase(invoices, notifier)
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
    decide = DecideInvoiceUseCase(invoices, notifier)

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
    decide = DecideInvoiceUseCase(invoices, notifier)

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
