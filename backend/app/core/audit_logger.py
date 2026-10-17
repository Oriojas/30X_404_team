"""
Módulo Core: Generador de Audit Log & Explicabilidad en Lenguaje Natural
Construye el payload explicable para el Dashboard web y notificaciones de Telegram.
"""

from typing import Dict, Any


class AuditLogger:
    """Generador de registros de auditoría y explicabilidad."""

    @staticmethod
    def build_audit_log(
        invoice_id: str,
        vendor_name: str,
        usd_amount: float,
        decision: str,
        evaluations: Dict[str, Any],
        explanation: str
    ) -> Dict[str, Any]:
        """Construye un objeto JSON de trazabilidad completa."""
        return {
            "invoice_id": invoice_id,
            "vendor_name": vendor_name,
            "usd_amount": usd_amount,
            "decision": decision,
            "evaluations": evaluations,
            "explanation_for_ui": explanation
        }
