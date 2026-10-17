"""
Módulo Core: Tubería de Evaluación de Reglas de Negocio en 4 Capas
1. Compliance / SARLAFT
2. Integridad & Duplicados
3. Solvencia Financiera
4. Gobierno Human-in-the-Loop (HITL)

Política de recorrido: una alerta REJECTED detiene la tubería de inmediato (las capas siguientes
quedan como NOT_EVALUATED). Las alertas SCALED_TO_HUMAN se acumulan para que el Audit Log muestre
todas las capas y se pueda aplicar HITL-03.
Los códigos y mensajes siguen la matriz de docs/reglas-negocio/reglas_pago_agente_v3.md.
"""

import unicodedata
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from app.core.domain.models import (
    CompanyRules,
    Decision,
    DecisionStatus,
    ExtractedInvoice,
    RuleAlert,
    TreasuryStatus,
    Vendor,
)

MIN_OCR_CONFIDENCE = 0.85
AMBIGUITY_ALERTS_THRESHOLD = 2
# Pequeñas inconsistencias de la factura que, acumuladas, disparan HITL-03
INCONSISTENCY_CODES = {"COMP-02", "COMP-04", "INTEG-02", "INTEG-03", "INTEG-04"}

PASSED, TRIGGERED, SKIPPED, NOT_EVALUATED = "PASSED", "TRIGGERED", "SKIPPED", "NOT_EVALUATED"
LAYERS = ("compliance_check", "integrity_check", "solvency_check", "hitl_check")


@dataclass
class EvaluationContext:
    """Hechos externos que el caso de uso reúne vía puertos antes de evaluar."""
    usd_amount: float
    fx_rate: float
    treasury: TreasuryStatus
    currency_supported: bool = True
    vendor: Optional[Vendor] = None
    sanctions_match: Optional[str] = None
    is_duplicate: bool = False
    vendor_has_history: bool = False
    # Factura vigente con el mismo archivo (SHA-256): INTEG-01 la cita en la explicación
    duplicate_of_invoice_id: Optional[int] = None


def format_usd(value: float) -> str:
    """Monto en USD para el Audit Log; los negativos como -$1,950.00 USD."""
    return f"{'-' if value < 0 else ''}${abs(value):,.2f} USD"


def _normalize(text: Optional[str]) -> str:
    plain = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return "".join(ch for ch in plain.lower() if ch.isalnum())


def _escalate(code: str, message: str) -> RuleAlert:
    return RuleAlert(code, DecisionStatus.SCALED_TO_HUMAN, message)


def _reject(code: str, message: str) -> RuleAlert:
    return RuleAlert(code, DecisionStatus.REJECTED, message)


class RulesPipeline:
    """Tubería secuencial y determinista para evaluar pagos corporativos."""

    def evaluate_invoice(
        self, invoice: ExtractedInvoice, context: EvaluationContext, rules: CompanyRules
    ) -> Decision:
        layers: List[tuple] = [
            ("compliance_check", self._compliance),
            ("integrity_check", self._integrity),
            ("solvency_check", self._solvency),
            ("hitl_check", self._hitl),
        ]
        evaluations: Dict[str, dict] = {name: {"status": NOT_EVALUATED, "alerts": []} for name in LAYERS}
        alerts: List[RuleAlert] = []

        for name, layer in layers:
            if name == "compliance_check" and not rules.sarlaft_check_enabled:
                evaluations[name] = {"status": SKIPPED, "alerts": [], "reason": "SARLAFT desactivado en las reglas"}
                continue
            if name == "solvency_check" and not context.currency_supported:
                evaluations[name] = {"status": SKIPPED, "alerts": [], "reason": "Monto sin conversión a USD"}
                continue

            layer_alerts = layer(invoice, context, rules, alerts)
            alerts.extend(layer_alerts)
            evaluations[name] = {
                "status": TRIGGERED if layer_alerts else PASSED,
                "alerts": [{"reason_code": a.code, "message": a.message} for a in layer_alerts],
            }
            if any(a.severity == DecisionStatus.REJECTED for a in layer_alerts):
                break

        evaluations["fx"] = {"usd_amount": context.usd_amount, "fx_rate_applied": context.fx_rate,
                             "blinka_fx_markup": "0.00 USD"}
        status = self._final_status(alerts)
        return Decision(status, self._explain(status, alerts, invoice, context), evaluations, alerts)

    def evaluate_solvency(self, usd_amount: float, treasury: TreasuryStatus, rules: CompanyRules) -> List[RuleAlert]:
        """Solo la Capa 3, con la tesorería vigente: la usa la revalidación al aprobar (F6.3)."""
        return self._solvency(None, EvaluationContext(usd_amount=usd_amount, fx_rate=1.0, treasury=treasury), rules, [])

    # ---------------------------------------------------------------- Capa 1
    def _compliance(self, invoice, ctx: EvaluationContext, rules, _prior) -> List[RuleAlert]:
        if ctx.sanctions_match:
            return [_reject("COMP-01", f"Rechazado por coincidencia con lista restrictiva internacional ({ctx.sanctions_match}).")]

        alerts = []
        vendor = ctx.vendor
        if vendor and invoice.bank_account and vendor.bank_account \
                and _normalize(invoice.bank_account) != _normalize(vendor.bank_account):
            alerts.append(_escalate("COMP-02", "Instrucciones bancarias no coinciden con las cuentas autorizadas del proveedor."))
        if vendor and vendor.is_pep:
            alerts.append(_escalate("COMP-03", "Escalado a Oficial de Cumplimiento por condición PEP del beneficiario."))
        if vendor and invoice.vendor_tax_id and invoice.vendor_name and (
            _normalize(invoice.vendor_tax_id) != _normalize(vendor.tax_id)
            or _normalize(invoice.vendor_name) != _normalize(vendor.legal_name)
        ):
            alerts.append(_escalate("COMP-04", f"Inconsistencia entre el NIT/razón social de la factura y el registro fiscal ({vendor.legal_name}, {vendor.tax_id})."))
        return alerts

    # ---------------------------------------------------------------- Capa 2
    def _integrity(self, invoice, ctx: EvaluationContext, rules: CompanyRules, _prior) -> List[RuleAlert]:
        if ctx.duplicate_of_invoice_id is not None:
            return [_reject("INTEG-01", f"Factura rechazada por cobro duplicado: el archivo es idéntico a la factura #{ctx.duplicate_of_invoice_id}, recibida en los últimos {rules.duplicate_check_days} días.")]
        if ctx.is_duplicate:
            return [_reject("INTEG-01", f"Factura rechazada por detección de cobro duplicado del mismo proveedor en los últimos {rules.duplicate_check_days} días.")]

        alerts = []
        if not ctx.currency_supported:
            alerts.append(_escalate("INTEG-04", f"Moneda {invoice.original_currency.upper()} no soportada por el FX Engine: no es posible normalizar el monto a USD. Requiere revisión."))
        contract = ctx.vendor.contract_amount_usd if ctx.vendor else None
        if ctx.currency_supported and contract is not None and ctx.usd_amount > contract:
            alerts.append(_escalate("INTEG-02", f"El valor cobrado ({format_usd(ctx.usd_amount)}) supera la tarifa acordada en el contrato ({format_usd(contract)})."))

        missing = [label for label, value in (("número de factura", invoice.invoice_number),
                                              ("proveedor", invoice.vendor_name)) if not value]
        if invoice.original_amount <= 0:
            missing.append("monto")
        if invoice.ocr_confidence_score < MIN_OCR_CONFIDENCE or missing:
            detail = f" Campos faltantes: {', '.join(missing)}." if missing else ""
            alerts.append(_escalate("INTEG-03", f"Lectura de factura ambigua o ilegible (confianza {invoice.ocr_confidence_score:.0%}). Requiere revisión.{detail}"))
        return alerts

    # ---------------------------------------------------------------- Capa 3
    def _solvency(self, invoice, ctx: EvaluationContext, rules: CompanyRules, _prior) -> List[RuleAlert]:
        alerts = []
        t = ctx.treasury
        # Solvencia contra el disponible: el saldo de la foto menos lo ya aprobado después de ella (F6.2)
        available = t.available_usd
        # FIN-04: tope duro. Sin conversión a USD, evaluate_invoice ya salta toda la Capa 3
        if ctx.usd_amount > rules.max_payment_usd:
            alerts.append(_reject("FIN-04", f"El pago de {format_usd(ctx.usd_amount)} supera el tope máximo por pago "
                                            f"definido por la empresa ({format_usd(rules.max_payment_usd)})."))
        liquidity = (f"Saldo {format_usd(t.balance_usd)}, comprometido en pagos aprobados {format_usd(t.committed_usd)}, "
                     f"disponible {format_usd(available)}.")
        if ctx.usd_amount > available:
            alerts.append(_escalate("FIN-01", f"Saldo disponible insuficiente en la cuenta Blinka para ejecutar el pago de {format_usd(ctx.usd_amount)}. {liquidity}"))
        elif available - ctx.usd_amount < rules.min_treasury_buffer_usd:
            alerts.append(_escalate("FIN-03", f"El pago de {format_usd(ctx.usd_amount)} dejaría la cuenta Blinka por debajo del colchón mínimo de tesorería ({format_usd(rules.min_treasury_buffer_usd)}). {liquidity}"))
        if t.month_spent_usd + ctx.usd_amount > t.monthly_budget_usd:
            alerts.append(_escalate("FIN-02", f"El pago excede el presupuesto disponible del período ({format_usd(t.monthly_budget_usd - t.month_spent_usd)} restantes de {format_usd(t.monthly_budget_usd)})."))
        return alerts

    # ---------------------------------------------------------------- Capa 4
    def _hitl(self, invoice, ctx: EvaluationContext, rules: CompanyRules, prior: List[RuleAlert]) -> List[RuleAlert]:
        alerts = []
        if ctx.currency_supported and ctx.usd_amount > rules.max_autonomous_usd:
            alerts.append(_escalate("HITL-01", f"El monto de {format_usd(ctx.usd_amount)} excede el límite autónomo de {format_usd(rules.max_autonomous_usd)}."))
        if not ctx.vendor or not ctx.vendor_has_history:
            alerts.append(_escalate("HITL-02", "Proveedor nuevo sin historial de pagos. Requiere verificación inicial por un operador."))
        inconsistencies = [a.code for a in prior if a.code in INCONSISTENCY_CODES]
        if len(inconsistencies) >= AMBIGUITY_ALERTS_THRESHOLD:
            alerts.append(_escalate("HITL-03", f"Acumulación de pequeñas inconsistencias detectadas ({', '.join(inconsistencies)})."))
        return alerts

    # ------------------------------------------------------------- Decisión
    @staticmethod
    def _final_status(alerts: List[RuleAlert]) -> DecisionStatus:
        if any(a.severity == DecisionStatus.REJECTED for a in alerts):
            return DecisionStatus.REJECTED
        if alerts:
            return DecisionStatus.SCALED_TO_HUMAN
        return DecisionStatus.AUTO_APPROVED

    @staticmethod
    def _explain(status: DecisionStatus, alerts: List[RuleAlert], invoice: ExtractedInvoice,
                 ctx: EvaluationContext) -> str:
        amount = format_usd(ctx.usd_amount)
        if not ctx.currency_supported:
            amount = f"{invoice.original_amount:,.2f} {invoice.original_currency.upper()} (sin conversión a USD)"
        elif invoice.original_currency.upper() != "USD":
            amount += f" ({invoice.original_amount:,.0f} {invoice.original_currency.upper()} a tasa {ctx.fx_rate:,.2f})"

        if status == DecisionStatus.AUTO_APPROVED:
            return (f"Pago aprobado automáticamente: {amount} dentro del límite autónomo, "
                    "proveedor verificado con historial, sin alertas de cumplimiento y saldo suficiente.")
        reasons = " ".join(f"[{a.code}] {a.message}" for a in alerts if a.severity == status)
        if status == DecisionStatus.REJECTED:
            return f"Pago frenado: {reasons}"
        return f"Pago de {amount} escalado a revisión humana: {reasons}"
