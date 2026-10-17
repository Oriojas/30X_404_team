"""
Composition Root
Único lugar donde se eligen los adaptadores concretos y se conectan a los puertos del Core.
Para cambiar Gemini, PostgreSQL o la fuente de tasas basta con modificar este archivo.
"""

from app.adapters.outbound.db.postgres_repository import (
    PostgresDatabase,
    PostgresIngestionLog,
    PostgresInvoiceRepository,
    PostgresRulesRepository,
    PostgresSanctionsRepository,
    PostgresTreasuryRepository,
    PostgresVendorRepository,
)
from app.adapters.outbound.fx.static_rates import StaticFXRateProvider
from app.adapters.outbound.notifications.channel_router import ChannelNotificationRouter
from app.adapters.outbound.ocr.gemini_ocr import GeminiOCRAdapter
from app.adapters.outbound.telegram.telegram_client import TelegramClient
from app.config import Settings
from app.core.domain.models import CompanyRules, TreasuryStatus
from app.core.domain.rules_pipeline import RulesPipeline
from app.core.use_cases import (
    DecideInvoiceUseCase,
    GetRulesUseCase,
    GetTreasuryUseCase,
    ListInvoicesUseCase,
    ProcessInvoiceUseCase,
    UpdateRulesUseCase,
)


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        company_id = settings.company_id
        default_rules = CompanyRules(
            company_id=company_id,
            max_autonomous_usd=settings.max_autonomous_usd,
            sarlaft_check_enabled=settings.sarlaft_check_enabled,
            duplicate_check_days=settings.duplicate_check_days,
        )
        # Sin fila de tesorería se asume saldo 0: toda factura escala (tolerancia cero)
        default_treasury = TreasuryStatus(balance_usd=0.0, monthly_budget_usd=0.0)

        # Adaptadores de salida
        self.db = PostgresDatabase(settings.database_url)
        self.telegram = TelegramClient(settings.telegram_bot_token)
        notifier = ChannelNotificationRouter({"TELEGRAM": self.telegram})
        invoice_repo = PostgresInvoiceRepository(self.db)
        rules_repo = PostgresRulesRepository(self.db, default_rules)
        treasury_repo = PostgresTreasuryRepository(self.db, default_treasury)

        # Casos de uso
        self.process_invoice = ProcessInvoiceUseCase(
            ocr=GeminiOCRAdapter(settings.gemini_api_key, settings.gemini_model),
            fx_rates=StaticFXRateProvider(),
            pipeline=RulesPipeline(),
            invoices=invoice_repo,
            rules=rules_repo,
            vendors=PostgresVendorRepository(self.db),
            sanctions=PostgresSanctionsRepository(self.db),
            treasury=treasury_repo,
            company_id=company_id,
            notifier=notifier,
            ingestion=PostgresIngestionLog(self.db),
        )
        self.decide_invoice = DecideInvoiceUseCase(invoice_repo, notifier=notifier)
        self.list_invoices = ListInvoicesUseCase(invoice_repo)
        self.get_rules = GetRulesUseCase(rules_repo, company_id)
        self.update_rules = UpdateRulesUseCase(rules_repo, company_id)
        self.get_treasury = GetTreasuryUseCase(treasury_repo, company_id)

    def status(self) -> dict:
        return {
            "environment": self.settings.environment,
            "database": "connected" if self.db.pool else "not_configured",
        }

    async def startup(self) -> None:
        await self.db.connect(auto_migrate=self.settings.db_auto_migrate, seed_demo=self.settings.db_seed_demo)

    async def shutdown(self) -> None:
        await self.db.close()
