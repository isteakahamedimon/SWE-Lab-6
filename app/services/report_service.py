from typing import Dict, Any, Optional
from datetime import date
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.notification_repository import NotificationRepository
from app.patterns.factory.report_factory import ReportFactory


class ReportService:
    def __init__(
        self,
        transaction_repo: Optional[TransactionRepository] = None,
        budget_repo: Optional[BudgetRepository] = None,
        notification_repo: Optional[NotificationRepository] = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository()
        self.budget_repo = budget_repo or BudgetRepository()
        self.notification_repo = notification_repo or NotificationRepository()

    def get_dashboard_summary(self, user_id: int) -> Dict[str, Any]:
        current_month = date.today().strftime("%Y-%m")

        all_time = self.transaction_repo.get_user_totals(user_id)
        month_totals = self.transaction_repo.get_monthly_totals_for_user(
            user_id, current_month
        )

        recent_txs = self.transaction_repo.filter_transactions(
            user_id=user_id, sort_by="date", sort_order="desc"
        )[:7]

        expense_breakdown = self.transaction_repo.get_category_breakdown(
            user_id=user_id, type_="expense", month_str=current_month
        )

        income_breakdown = self.transaction_repo.get_category_breakdown(
            user_id=user_id, type_="income", month_str=current_month
        )

        monthly_history = self.transaction_repo.get_monthly_summary(
            user_id=user_id, limit_months=6
        )

        unread_notifications = self.notification_repo.get_by_user(
            user_id=user_id, unread_only=True
        )

        return {
            "current_month": current_month,
            "all_time": all_time,
            "month_totals": month_totals,
            "recent_transactions": recent_txs,
            "expense_breakdown": expense_breakdown,
            "income_breakdown": income_breakdown,
            "monthly_history": monthly_history,
            "unread_notifications": unread_notifications,
        }

    def generate_report(
        self, report_type: str, user_id: int, **kwargs
    ) -> Dict[str, Any]:
        report = ReportFactory.create_report(report_type)
        context = {
            "transaction_repo": self.transaction_repo,
            "budget_repo": self.budget_repo,
            **kwargs,
        }
        return report.generate(user_id, context)
