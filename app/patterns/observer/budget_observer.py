import logging
from app.patterns.observer.subject import TransactionObserver

logger = logging.getLogger(__name__)


class BudgetAlertObserver(TransactionObserver):
    """
    Observer that checks if category expenses cross 80% or 100% of a defined monthly budget.
    If so, it generates a notification record for the user.
    """

    def __init__(self, budget_repo=None, transaction_repo=None, notification_repo=None):
        self.budget_repo = budget_repo
        self.transaction_repo = transaction_repo
        self.notification_repo = notification_repo

    def on_transaction_event(self, event_type: str, transaction) -> None:
        if getattr(transaction, "type", None) != "expense":
            return

        # Lazy load repositories if not injected (allows runtime DI or test mock DI)
        if not self.budget_repo:
            from app.repositories.budget_repository import BudgetRepository
            self.budget_repo = BudgetRepository()
        if not self.transaction_repo:
            from app.repositories.transaction_repository import TransactionRepository
            self.transaction_repo = TransactionRepository()
        if not self.notification_repo:
            from app.repositories.notification_repository import NotificationRepository
            self.notification_repo = NotificationRepository()

        t_date = transaction.date
        month_str = t_date.strftime("%Y-%m")
        user_id = transaction.user_id
        category_id = transaction.category_id

        budget = self.budget_repo.get_by_category_and_month(user_id, category_id, month_str)
        if not budget or budget.amount <= 0:
            return

        spent = self.transaction_repo.get_expense_by_category_for_month(
            user_id, category_id, month_str
        )
        pct = (spent / budget.amount) * 100.0
        cat_name = transaction.category.name if getattr(transaction, "category", None) else "Category"

        if pct >= 100.0:
            self.notification_repo.create(
                user_id=user_id,
                title="Budget Exceeded!",
                message=f"You have spent ${spent:.2f} of your ${budget.amount:.2f} budget for {cat_name} in {month_str} ({pct:.0f}%).",
                level="danger",
            )
        elif pct >= 80.0:
            self.notification_repo.create(
                user_id=user_id,
                title="Budget Warning",
                message=f"You have spent ${spent:.2f} of your ${budget.amount:.2f} budget for {cat_name} in {month_str} ({pct:.0f}%).",
                level="warning",
            )
