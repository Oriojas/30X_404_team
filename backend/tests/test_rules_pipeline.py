"""Pruebas de la tubería de 4 capas: Test Suite TC-01..TC-07 de reglas_pago_agente_v3 y reglas adicionales."""

from app.core.domain.models import CompanyRules, DecisionStatus, ExtractedInvoice, TreasuryStatus, Vendor
from app.core.domain.rules_pipeline import EvaluationContext, RulesPipeline

RULES = CompanyRules(company_id="TEST")
AWS = Vendor("US-91-1646860", "Amazon Web Services LATAM", "US-CHASE-000123456", contract_amount_usd=1000)
NUBE = Vendor("901.223.450-1", "Nube Andina Consultores S.A.S.", "CO-DAVIVIENDA-55566677788", contract_amount_usd=5000)


def evaluate(amount, vendor=AWS, *, name=None, tax_id=None, bank=None, currency="USD", rate=1.0,
             history=True, duplicate=False, sanctions=None, balance=8500, budget=25000, spent=0, committed=0,
             confidence=1.0, rules=RULES):
    invoice = ExtractedInvoice(
        invoice_number="F-1", vendor_name=name or (vendor.legal_name if vendor else "Proveedor X"),
        vendor_tax_id=tax_id, bank_account=bank, original_amount=amount * rate,
        original_currency=currency, ocr_confidence_score=confidence,
    )
    context = EvaluationContext(
        usd_amount=amount, fx_rate=rate, treasury=TreasuryStatus(balance, budget, spent, committed), vendor=vendor,
        sanctions_match=sanctions, is_duplicate=duplicate, vendor_has_history=history,
    )
    return RulesPipeline().evaluate_invoice(invoice, context, rules)


def codes(decision):
    return [a.code for a in decision.alerts]


def test_tc01_recurring_invoice_is_auto_approved():
    decision = evaluate(450)
    assert decision.status == DecisionStatus.AUTO_APPROVED
    assert codes(decision) == []
    assert all(decision.evaluations[layer]["status"] == "PASSED"
               for layer in ("compliance_check", "integrity_check", "solvency_check", "hitl_check"))


def test_tc02_duplicate_is_rejected_and_stops_pipeline():
    decision = evaluate(1200, duplicate=True)
    assert decision.status == DecisionStatus.REJECTED
    assert codes(decision) == ["INTEG-01"]
    assert decision.evaluations["solvency_check"]["status"] == "NOT_EVALUATED"


def test_tc03_new_vendor_is_scaled():
    decision = evaluate(800, vendor=None, name="Diseño Creativo Bogotá S.A.S.", history=False)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert codes(decision) == ["HITL-02"]


def test_tc04_amount_over_autonomous_limit_is_scaled():
    decision = evaluate(3500, vendor=NUBE)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert codes(decision) == ["HITL-01"]
    assert "$3,500.00 USD" in decision.explanation


def test_tc05_insufficient_balance_is_scaled():
    vendor = Vendor("LEM850101AB1", "Logística Express MX S.A. de C.V.", contract_amount_usd=15000)
    decision = evaluate(10000, vendor=vendor, balance=4000)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert "FIN-01" in codes(decision)


def test_tc06_sanctioned_account_is_rejected_at_layer_one():
    decision = evaluate(900, sanctions="OFAC: Global Trade Partners Ltd")
    assert decision.status == DecisionStatus.REJECTED
    assert codes(decision) == ["COMP-01"]
    assert decision.evaluations["integrity_check"]["status"] == "NOT_EVALUATED"


def test_tc07_amount_over_agreed_rate_is_scaled_only_by_integ02():
    decision = evaluate(1500)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert codes(decision) == ["INTEG-02"]
    assert "$1,000.00 USD" in decision.explanation


def test_foreign_currency_explanation_includes_fx_details():
    decision = evaluate(357.14, currency="COP", rate=4200)
    assert decision.status == DecisionStatus.AUTO_APPROVED
    assert "COP a tasa 4,200.00" in decision.explanation
    assert decision.evaluations["fx"]["blinka_fx_markup"] == "0.00 USD"


def test_bank_account_mismatch_and_pep_are_scaled():
    pep = Vendor(AWS.tax_id, AWS.legal_name, AWS.bank_account, is_pep=True, contract_amount_usd=1000)
    decision = evaluate(450, vendor=pep, bank="CO-OTRA-CUENTA-1")
    assert codes(decision) == ["COMP-02", "COMP-03"]


def test_tax_id_name_mismatch_is_scaled():
    decision = evaluate(450, name="Otra Empresa S.A.S.", tax_id=AWS.tax_id)
    assert codes(decision) == ["COMP-04"]


def test_accumulated_inconsistencies_trigger_hitl03():
    decision = evaluate(1500, bank="CO-OTRA-CUENTA-1", confidence=0.6)
    assert codes(decision) == ["COMP-02", "INTEG-02", "INTEG-03", "HITL-03"]


def test_treasury_buffer_and_budget():
    decision = evaluate(900, balance=1500, budget=25000, spent=24500)
    assert codes(decision) == ["FIN-03", "FIN-02"]


def test_compliance_layer_skipped_when_disabled():
    rules = CompanyRules(company_id="TEST", sarlaft_check_enabled=False)
    decision = evaluate(450, sanctions="OFAC: X", rules=rules)
    assert decision.status == DecisionStatus.AUTO_APPROVED
    assert decision.evaluations["compliance_check"]["status"] == "SKIPPED"


def test_empty_ocr_extraction_is_scaled_for_review():
    invoice = ExtractedInvoice(invoice_number=None, vendor_name=None, original_amount=0.0, ocr_confidence_score=0.0)
    context = EvaluationContext(usd_amount=0.0, fx_rate=1.0, treasury=TreasuryStatus(8500, 25000))
    decision = RulesPipeline().evaluate_invoice(invoice, context, RULES)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert "INTEG-03" in codes(decision)


def test_unsupported_currency_is_scaled_without_misleading_amounts():
    invoice = ExtractedInvoice(invoice_number="F-9", vendor_name=AWS.legal_name, original_amount=1000,
                               original_currency="GBP")
    context = EvaluationContext(usd_amount=0.0, fx_rate=0.0, currency_supported=False,
                                treasury=TreasuryStatus(8500, 25000), vendor=AWS, vendor_has_history=True)
    decision = RulesPipeline().evaluate_invoice(invoice, context, RULES)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert codes(decision) == ["INTEG-04"]
    assert decision.evaluations["solvency_check"]["status"] == "SKIPPED"
    assert "1,000.00 GBP (sin conversión a USD)" in decision.explanation


def test_fin01_evalua_contra_el_disponible_y_no_contra_el_saldo():
    # $1,900 cabe en el saldo de $8,500, pero no en los $1,500 que quedan tras $7,000 comprometidos
    decision = evaluate(1900, vendor=NUBE, balance=8500, committed=7000)
    assert decision.status == DecisionStatus.SCALED_TO_HUMAN
    assert codes(decision) == ["FIN-01"]
    message = decision.alerts[0].message
    assert "$8,500.00 USD" in message and "$7,000.00 USD" in message and "$1,500.00 USD" in message


def test_fin03_evalua_el_colchon_contra_el_disponible():
    # Disponible $2,800: pagar $1,900 deja $900, bajo el colchón de $1,000
    decision = evaluate(1900, vendor=NUBE, balance=8500, committed=5700)
    assert codes(decision) == ["FIN-03"]
    assert "disponible $2,800.00 USD" in decision.alerts[0].message


def test_cinco_facturas_que_caben_solas_pero_no_juntas():
    """Con $8,500 y $1,000 de colchón, solo tres de cinco facturas de $1,900 salen aprobadas solas."""
    committed, statuses = 0.0, []
    for _ in range(5):
        decision = evaluate(1900, vendor=NUBE, balance=8500, committed=committed)
        statuses.append(decision.status)
        if decision.status == DecisionStatus.AUTO_APPROVED:
            committed += 1900
    assert statuses == [DecisionStatus.AUTO_APPROVED] * 3 + [DecisionStatus.SCALED_TO_HUMAN] * 2
    assert committed == 5700 <= 8500 - RULES.min_treasury_buffer_usd

