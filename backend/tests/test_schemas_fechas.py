"""Las fechas del Audit Log salen marcadas como UTC: la base guarda TIMESTAMP sin zona, siempre en UTC,
y el navegador debe convertirlas a su hora local (F5.8)."""

from datetime import datetime, timedelta, timezone

from app.adapters.inbound.api.schemas import InvoiceResponse


def invoice(**fechas):
    return InvoiceResponse(
        invoice_number="F-1", vendor_name="Proveedor", original_amount=100, original_currency="USD",
        usd_amount=100, channel_source="API", decision_status="AUTO_APPROVED", audit_explanation="ok", **fechas,
    )


def test_fecha_sin_zona_sale_como_utc_con_z():
    body = invoice(processed_at=datetime(2026, 10, 17, 12, 41, 1), decided_at=datetime(2026, 10, 17, 12, 45)).model_dump(mode="json")
    assert body["processed_at"] == "2026-10-17T12:41:01Z"
    assert body["decided_at"] == "2026-10-17T12:45:00Z"


def test_fecha_con_zona_se_convierte_a_utc_y_la_ausente_sigue_nula():
    bogota = timezone(timedelta(hours=-5))
    body = invoice(processed_at=datetime(2026, 10, 17, 7, 41, 1, tzinfo=bogota)).model_dump(mode="json")
    assert body["processed_at"] == "2026-10-17T12:41:01Z"
    assert body["decided_at"] is None
