"""
Ingesta idempotente en el caso de uso ProcessInvoice (Fase 2):
transporte por (canal, external_id) y negocio por SHA-256 del archivo (INTEG-01).
"""

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from app.core.domain.models import DecisionStatus, ExtractedInvoice, IngestionStatus, Vendor
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import ProcessInvoiceUseCase

from .fakes import (
    FakeRates, FixedTreasury, InMemoryIngestionLog, InMemoryInvoices, InMemoryRules, InMemoryVendors, NoSanctions,
    SpyNotifier,
)

VENDOR = Vendor("900.584.112-4", "DevStudio LatAm S.A.S.", contract_amount_usd=5000)


class CountingOCR:
    """OCR falso que cuenta llamadas, cede el turno (simula latencia) y puede fallar la primera vez."""

    def __init__(self, extracted, fail_first=False):
        self.extracted, self.fail_first, self.calls = extracted, fail_first, 0

    async def extract_invoice_data(self, file_bytes, mime_type):
        self.calls += 1
        await asyncio.sleep(0)
        if self.fail_first and self.calls == 1:
            raise RuntimeError("Gemini no disponible")
        return self.extracted


def cop_invoice(number="DS-1", amount=1_500_000):
    return ExtractedInvoice(invoice_number=number, vendor_name=VENDOR.legal_name,
                            original_amount=amount, original_currency="COP", ocr_confidence_score=0.95)


def build(extracted=None, fail_first=False):
    ocr = CountingOCR(extracted or cop_invoice(), fail_first)
    invoices, notifier, log = InMemoryInvoices(), SpyNotifier(), InMemoryIngestionLog()
    use_case = ProcessInvoiceUseCase(
        ocr=ocr, fx_rates=FakeRates(), pipeline=RulesPipeline(), invoices=invoices, rules=InMemoryRules(),
        vendors=InMemoryVendors(VENDOR), sanctions=NoSanctions(), treasury=FixedTreasury(), company_id="TEST",
        notifier=notifier, ingestion=log,
    )
    return use_case, ocr, invoices, notifier, log


def test_misma_entrega_se_procesa_una_vez_sin_avisos_duplicados():
    use_case, ocr, invoices, notifier, _ = build()

    first = asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=42, external_id="1001"))
    again = asyncio.run(use_case.from_document(b"img", "image/jpeg", "TELEGRAM", chat_id=42, external_id="1001"))

    assert not first.duplicate and again.duplicate and not again.in_progress
    assert again.invoice.id == first.invoice.id
    assert len(invoices.items) == 1 and ocr.calls == 1
    assert len(notifier.received) == 1 and len(notifier.decisions) == 1


def test_carga_manual_repetida_devuelve_la_misma_factura():
    use_case, _, invoices, notifier, _ = build()
    first = asyncio.run(use_case.from_extracted(cop_invoice(), "API", external_id="k-1"))
    again = asyncio.run(use_case.from_extracted(cop_invoice(), "API", external_id="k-1"))
    assert again.duplicate and again.invoice.id == first.invoice.id
    assert len(invoices.items) == 1 and len(notifier.decisions) == 1


def test_entrega_en_proceso_se_informa_sin_factura():
    use_case, _, _, notifier, log = build()
    asyncio.run(log.claim("WEB", "k-1"))  # otra solicitud la reclamó y no ha terminado

    result = asyncio.run(use_case.from_document(b"img", "image/jpeg", "WEB", external_id="k-1"))
    assert result.duplicate and result.in_progress and result.invoice is None
    assert notifier.received == [] and notifier.decisions == []


def test_sin_external_id_cada_entrega_se_procesa():
    use_case, _, invoices, _, _ = build()
    asyncio.run(use_case.from_extracted(cop_invoice("A"), "API"))
    asyncio.run(use_case.from_extracted(cop_invoice("B", 2_000_000), "API"))
    assert len(invoices.items) == 2


def test_falla_libera_la_clave_y_el_reintento_procesa():
    use_case, ocr, invoices, _, log = build(fail_first=True)

    with pytest.raises(RuntimeError):
        asyncio.run(use_case.from_document(b"img", "image/jpeg", "WEB", external_id="k-1"))
    assert ("WEB", "k-1") not in log.records and invoices.items == {}

    retry = asyncio.run(use_case.from_document(b"img", "image/jpeg", "WEB", external_id="k-1"))
    assert not retry.duplicate and retry.invoice.id == 1 and ocr.calls == 2
    assert log.records[("WEB", "k-1")].status == IngestionStatus.COMPLETED


def test_solicitudes_concurrentes_con_la_misma_clave_procesan_una_sola_vez():
    use_case, ocr, invoices, notifier, _ = build()

    async def race():
        return await asyncio.gather(*[
            use_case.from_document(b"img", "image/jpeg", "WEB", external_id="k-1") for _ in range(3)
        ])

    results = asyncio.run(race())
    assert sum(not r.duplicate for r in results) == 1
    assert len(invoices.items) == 1 and ocr.calls == 1 and len(notifier.decisions) == 1


def test_mismo_archivo_por_otro_canal_salta_el_ocr_y_se_rechaza_por_integ01():
    use_case, ocr, invoices, notifier, _ = build()
    original = asyncio.run(use_case.from_document(b"factura", "image/png", "TELEGRAM", chat_id=7, external_id="1"))
    assert original.invoice.decision_status == DecisionStatus.SCALED_TO_HUMAN  # HITL-02, vigente
    assert len(original.invoice.file_sha256) == 64

    copy = asyncio.run(use_case.from_document(b"factura", "image/png", "WEB", external_id="otra-clave")).invoice
    assert ocr.calls == 1
    assert copy.decision_status == DecisionStatus.REJECTED
    assert "INTEG-01" in copy.audit_explanation and f"#{original.invoice.id}" in copy.audit_explanation
    assert copy.invoice_number == original.invoice.invoice_number and copy.file_sha256 == original.invoice.file_sha256
    assert len(invoices.items) == 2 and len(notifier.decisions) == 2  # entrega de negocio distinta: sí se avisa


def test_archivo_ilegible_repetido_igual_se_frena_por_hash():
    empty = ExtractedInvoice(invoice_number=None, vendor_name=None, original_amount=0.0, ocr_confidence_score=0.0)
    use_case, ocr, _, _, _ = build(empty)
    first = asyncio.run(use_case.from_document(b"borrosa", "image/jpeg", "WEB")).invoice
    assert first.decision_status == DecisionStatus.SCALED_TO_HUMAN  # INTEG-03

    second = asyncio.run(use_case.from_document(b"borrosa", "image/jpeg", "TELEGRAM", chat_id=1)).invoice
    assert second.decision_status == DecisionStatus.REJECTED and "INTEG-01" in second.audit_explanation
    assert ocr.calls == 1


def test_hash_de_factura_rechazada_o_fuera_de_ventana_se_procesa_normal():
    use_case, ocr, invoices, _, _ = build()
    first = asyncio.run(use_case.from_document(b"factura", "image/png", "WEB")).invoice

    invoices.items[first.id] = replace(first, decision_status=DecisionStatus.HUMAN_REJECTED)
    asyncio.run(use_case.from_document(b"factura", "image/png", "WEB"))
    assert ocr.calls == 2

    for invoice_id, invoice in invoices.items.items():
        invoices.items[invoice_id] = replace(invoice, processed_at=datetime.utcnow() - timedelta(days=40))
    asyncio.run(use_case.from_document(b"factura", "image/png", "WEB"))
    assert ocr.calls == 3
