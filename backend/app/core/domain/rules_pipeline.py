"""
Módulo Core: Tubería de Evaluación de Reglas de Negocio en 4 Capas
1. Compliance / SARLAFT
2. Integridad & Duplicados
3. Solvencia Financiera
4. Gobierno Human-in-the-Loop (HITL)
"""

from dataclasses import dataclass

from .models import CompanyRules, Decision, DecisionStatus, ExtractedInvoice


@dataclass
class EvaluationContext:
    """Hechos externos que el caso de uso reúne vía puertos antes de evaluar."""
    usd_amount: float
    is_duplicate: bool = False


class RulesPipeline:
    """Tubería secuencial y determinista para evaluar pagos corporativos."""

    def evaluate_invoice(
        self, invoice: ExtractedInvoice, context: EvaluationContext, rules: CompanyRules
    ) -> Decision:
        """Evalúa secuencialmente las 4 capas de negocio."""
        # TODO: Implementar lógica capa a capa
        return Decision(
            status=DecisionStatus.AUTO_APPROVED,
            explanation="Pago aprobado automáticamente al cumplir 100% de criterios.",
        )
