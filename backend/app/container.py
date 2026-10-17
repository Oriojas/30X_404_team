"""
Composition Root
Único lugar donde se eligen los adaptadores concretos y se conectan a los puertos del Core.
Para cambiar Gemini, PostgreSQL o la fuente de tasas basta con modificar este archivo.
"""

from .adapters.outbound.db.postgres_repository import PostgresInvoiceRepository, PostgresRulesRepository
from .adapters.outbound.fx.static_rates import StaticFXRateProvider
from .adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter
from .adapters.outbound.telegram.telegram_client import TelegramClient
from .config import Settings
from .core.domain.fx_converter import FXConverter
from .core.domain.models import CompanyRules
from .core.domain.rules_pipeline import RulesPipeline
from .core.use_cases import (
    GetRulesUseCase,
    ListInvoicesUseCase,
    ProcessInvoiceUseCase,
    UpdateRulesUseCase,
)


class Container:
    def __init__(self, settings: Settings):
        default_rules = CompanyRules(
            company_id=settings.company_id,
            max_autonomous_usd=settings.max_autonomous_usd,
            sarlaft_check_enabled=settings.sarlaft_check_enabled,
            duplicate_check_days=settings.duplicate_check_days,
        )

        # Adaptadores de salida
        self.telegram = TelegramClient(settings.telegram_bot_token)
        invoice_repo = PostgresInvoiceRepository(settings.database_url)
        rules_repo = PostgresRulesRepository(settings.database_url, default_rules)
        ocr = GeminiOCRAdapter(settings.gemini_api_key, settings.gemini_model)
        fx_converter = FXConverter(StaticFXRateProvider())

        # Casos de uso
        self.process_invoice = ProcessInvoiceUseCase(
            ocr=ocr,
            fx_converter=fx_converter,
            pipeline=RulesPipeline(),
            invoices=invoice_repo,
            rules=rules_repo,
            notifier=self.telegram,
            company_id=settings.company_id,
        )
        self.list_invoices = ListInvoicesUseCase(invoice_repo)
        self.get_rules = GetRulesUseCase(rules_repo, settings.company_id)
        self.update_rules = UpdateRulesUseCase(rules_repo, settings.company_id)
