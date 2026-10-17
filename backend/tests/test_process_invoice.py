"""
Pruebas de los casos de uso ProcessInvoice y DecideInvoice con adaptadores falsos.
Demuestran que el Core funciona sin Gemini, PostgreSQL ni Telegram.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.core.domain.errors import (
    InvalidDecisionStateError, InvoiceNotFoundError, PaymentCapExceededError, UnconvertedAmountApprovalError,
)
from app.core.domain.models import DecisionStatus, ExtractedInvoice, HumanDecision, ProcessedInvoice, Vendor
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import (
    CreateVendorUseCase, DecideInvoiceUseCase, ProcessInvoiceUseCase, UpdateRulesUseCase, UpdateVendorUseCase,
)

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


NEW_VENDOR = "Diseño Creativo Bogotá S.A.S."


def new_vendor_invoice(number="DC-1", amount=1_500_000):
    """Proveedor fuera de la lista permitida: escala solo por HITL-02 (sin alertas FIN)."""
    return ExtractedInvoice(invoice_number=number, vendor_name=NEW_VENDOR, vendor_tax_id="901.555.010-2",
                            original_amount=amount, original_currency="COP")


def test_vendor_outside_the_allowlist_is_scaled_then_registered_vendor_is_approved_and_duplicate_rejected():
    use_case, invoices, notifier = build(new_vendor_invoice())

    first = asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=42)).invoice
    assert first.usd_amount == 357.14 and first.fx_rate_applied == 4200.0
    assert first.decision_status == DecisionStatus.SCALED_TO_HUMAN
    assert "HITL-02" in first.audit_explanation and "fuera de la lista permitida" in first.audit_explanation
    assert notifier.received == [("TELEGRAM", 42)]
    assert notifier.decisions[-1].source_chat_id == 42

    decide = decider(invoices, notifier)
    approved = asyncio.run(decide.execute(first.id, HumanDecision.APPROVE, "CFO Blinka", "Proveedor validado"))
    assert approved.decision_status == DecisionStatus.HUMAN_APPROVED
    assert approved.decided_by == "CFO Blinka" and "Proveedor validado" in approved.audit_explanation

    # El alta desde el dashboard es la verificación inicial: la siguiente factura ya no escala (F7.4)
    asyncio.run(CreateVendorUseCase(use_case.vendors).execute(
        "901.555.010-2", NEW_VENDOR, "CO-BANCOLOMBIA-55500011122", 5000, "CFO Blinka"))
    second = asyncio.run(use_case.from_extracted(new_vendor_invoice("DC-2", 2_100_000), "API")).invoice
    assert second.decision_status == DecisionStatus.AUTO_APPROVED
    assert "proveedor activo en la lista permitida" in second.audit_explanation

    repeated = asyncio.run(use_case.from_extracted(new_vendor_invoice("DC-2", 2_100_000), "API")).invoice
    assert repeated.decision_status == DecisionStatus.REJECTED
    assert "INTEG-01" in repeated.audit_explanation


def test_human_decision_only_applies_to_scaled_invoices():
    use_case, invoices, notifier = build(new_vendor_invoice())
    decide = decider(invoices, notifier)

    with pytest.raises(InvoiceNotFoundError):
        asyncio.run(decide.execute(99, HumanDecision.APPROVE, "CFO"))

    scaled = asyncio.run(use_case.from_extracted(new_vendor_invoice(), "API")).invoice
    rejected = asyncio.run(decide.execute(scaled.id, HumanDecision.REJECT, "CFO"))
    assert rejected.decision_status == DecisionStatus.HUMAN_REJECTED

    with pytest.raises(InvalidDecisionStateError):
        asyncio.run(decide.execute(scaled.id, HumanDecision.APPROVE, "CFO"))


def test_concurrent_human_decisions_only_one_wins():
    use_case, invoices, notifier = build(new_vendor_invoice())
    scaled = asyncio.run(use_case.from_extracted(new_vendor_invoice(), "API")).invoice
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
    use_case, invoices, notifier = build(new_vendor_invoice())
    scaled = asyncio.run(use_case.from_extracted(new_vendor_invoice(), "API")).invoice  # HITL-02 (fuera de la lista), no FIN
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
    """Tesorería que compromete lo aprobado ($8,500, colchón $1,000) y una factura aprobada antes de la foto."""
    invoices = InMemoryInvoices()
    # Aprobada antes de la foto: no compromete
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



def test_aprobar_por_encima_de_un_tope_rebajado_responde_conflicto_y_rechazar_si_funciona():
    # Escaló con el tope por defecto; luego la empresa bajó el tope por debajo del monto (F7.2, D5)
    use_case, invoices, notifier = build(new_vendor_invoice())
    scaled = asyncio.run(use_case.from_extracted(new_vendor_invoice(), "API")).invoice
    rules = InMemoryRules(max_autonomous_usd=100, max_payment_usd=100)
    decide = DecideInvoiceUseCase(invoices, FixedTreasury(), rules, "TEST", notifier)

    with pytest.raises(PaymentCapExceededError, match="FIN-04|tope máximo"):
        asyncio.run(decide.execute(scaled.id, HumanDecision.APPROVE, "CFO"))
    assert invoices.items[scaled.id].decision_status == DecisionStatus.SCALED_TO_HUMAN

    rejected = asyncio.run(decide.execute(scaled.id, HumanDecision.REJECT, "CFO"))
    assert rejected.decision_status == DecisionStatus.HUMAN_REJECTED


def test_bajar_el_tope_cambia_la_decision_de_la_siguiente_factura():
    rules = InMemoryRules()
    use_case = ProcessInvoiceUseCase(
        ocr=FakeOCR(None), fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=InMemoryInvoices(), rules=rules,
        vendors=InMemoryVendors(VENDOR), sanctions=NoSanctions(), treasury=FixedTreasury(), company_id="TEST",
    )
    first = asyncio.run(use_case.from_extracted(cop_invoice("DS-1"), "API")).invoice
    assert first.decision_status != DecisionStatus.REJECTED

    asyncio.run(UpdateRulesUseCase(rules, "TEST").execute({"max_autonomous_usd": 100, "max_payment_usd": 100}))
    # Otro monto: con el mismo, INTEG-01 la rechazaría como duplicada antes de llegar a la Capa 3
    second = asyncio.run(use_case.from_extracted(cop_invoice("DS-2", amount=1_600_000), "API")).invoice
    assert second.decision_status == DecisionStatus.REJECTED and "FIN-04" in second.audit_explanation


@pytest.mark.parametrize("tax_id, name", [
    ("900584112-4", "Otro nombre"),                  # NIT sin puntos: el NIT manda
    (None, "DevStudio LatAm SAS"),                   # sin NIT, razón social sin puntos
    (None, "devstudio latam s.a.s"),
])
def test_proveedor_registrado_se_encuentra_aunque_el_ocr_lo_lea_con_otro_formato(tax_id, name):
    # La etiqueta ("NIT 900...") sí cambiaría la llave: el prompt de Gemini pide el número sin ella
    found = asyncio.run(InMemoryVendors(VENDOR).find(tax_id, name))
    assert found is not None and found.tax_id == VENDOR.tax_id


def test_razon_social_vacia_o_solo_signos_no_empata():
    assert asyncio.run(InMemoryVendors(VENDOR).find(None, "...")) is None
    assert asyncio.run(InMemoryVendors(VENDOR).find(None, None)) is None


def test_baja_logica_hace_escalar_la_siguiente_factura_y_reactivar_la_aprueba():
    use_case, _, _ = build(cop_invoice())
    vendor_id = asyncio.run(use_case.vendors.find(VENDOR.tax_id, None)).id
    update = UpdateVendorUseCase(use_case.vendors)

    asyncio.run(update.execute(vendor_id, {"active": False}, "CFO Demo"))
    off = asyncio.run(use_case.from_extracted(cop_invoice("DS-10", 1_000_000), "API")).invoice
    assert off.decision_status == DecisionStatus.SCALED_TO_HUMAN and "inactivo" in off.audit_explanation

    asyncio.run(update.execute(vendor_id, {"active": True}, "CFO Demo"))
    on = asyncio.run(use_case.from_extracted(cop_invoice("DS-11", 1_100_000), "API")).invoice
    assert on.decision_status == DecisionStatus.AUTO_APPROVED


def test_subir_la_tarifa_acordada_quita_integ02_de_la_siguiente_factura():
    use_case, _, _ = build(cop_invoice())
    vendor_id = asyncio.run(use_case.vendors.find(VENDOR.tax_id, None)).id
    asyncio.run(UpdateVendorUseCase(use_case.vendors).execute(vendor_id, {"contract_amount_usd": 300}, "CFO"))
    over = asyncio.run(use_case.from_extracted(cop_invoice("DS-20", 1_500_000), "API")).invoice  # $357 > $300
    assert "INTEG-02" in over.audit_explanation

    asyncio.run(UpdateVendorUseCase(use_case.vendors).execute(vendor_id, {"contract_amount_usd": 400}, "CFO"))
    within = asyncio.run(use_case.from_extracted(cop_invoice("DS-21", 1_520_000), "API")).invoice  # $361.90
    assert within.decision_status == DecisionStatus.AUTO_APPROVED
