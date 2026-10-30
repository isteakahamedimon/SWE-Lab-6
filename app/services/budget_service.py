from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository


class BudgetService:
    def __init__(
        self,
        budget_repo: Optional[BudgetRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
    ):
        self.budget_repo = budget_repo or BudgetRepository()
        self.category_repo = category_repo or CategoryRepository()
        self.transaction_repo = transaction_repo or TransactionRepository()

    def get_budget_by_id(self, budget_id: int, user_id: int) -> Optional[Budget]:
        b = self.budget_repo.get_by_id(budget_id)
        if b and b.user_id == user_id:
            return b
        return None

    def get_user_budgets(self, user_id: int, month: Optional[str] = None) -> List[Budget]:
        if month:
            return self.budget_repo.get_by_user_and_month(user_id, month)
        return self.budget_repo.get_by_user(user_id)

    def set_budget(
        self, user_id: int, category_id: int, month: str, amount: float
    ) -> Tuple[Optional[Budget], Optional[str]]:
        category = self.category_repo.get_by_id(category_id)
        if not category or category.user_id != user_id:
            return None, "Invalid category selected."

        if category.type != "expense":
            return None, "Budgets can only be set for expense categories."

        month = month.strip()
        if len(month) != 7 or month[4] != "-":
            return None, "Month must be in YYYY-MM format."

        try:
            val_amount = float(amount)
        except (ValueError, TypeError):
            return None, "Budget amount must be a valid number."

        if val_amount <= 0:
            return None, "Budget amount must be greater than zero."

        # Check if already exists for this category and month
        existing = self.budget_repo.get_by_category_and_month(user_id, category_id, month)
        if existing:
            existing.amount = round(val_amount, 2)
            self.budget_repo.update(existing)
            return existing, None

        budget = self.budget_repo.create(
            user_id=user_id,
            category_id=category_id,
            month=month,
            amount=round(val_amount, 2),
        )
        return budget, None

    def update_budget(
        self, budget_id: int, user_id: int, amount: float
    ) -> Tuple[Optional[Budget], Optional[str]]:
        budget = self.get_budget_by_id(budget_id, user_id)
        if not budget:
            return None, "Budget not found."

        try:
            val_amount = float(amount)
        except (ValueError, TypeError):
            return None, "Budget amount must be a valid number."

        if val_amount <= 0:
            return None, "Budget amount must be greater than zero."

        budget.amount = round(val_amount, 2)
        self.budget_repo.update(budget)
        return budget, None

    def delete_budget(self, budget_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        budget = self.get_budget_by_id(budget_id, user_id)
        if not budget:
            return False, "Budget not found."

        self.budget_repo.delete(budget)
        return True, None

    def get_budget_overview(
        self, user_id: int, month: Optional[str] = None
    ) -> Dict[str, Any]:
        if not month:
            month = date.today().strftime("%Y-%m")

        budgets = self.budget_repo.get_by_user_and_month(user_id, month)
        items = []
        total_budget = 0.0
        total_spent = 0.0

        for b in budgets:
            spent = self.transaction_repo.get_expense_by_category_for_month(
                user_id, b.category_id, month
            )
            pct = (spent / b.amount * 100.0) if b.amount > 0 else 0.0
            remaining = b.amount - spent

            if pct >= 100.0:
                status = "Exceeded"
                status_color = "danger"
            elif pct >= 80.0:
                status = "Warning"
                status_color = "warning"
            else:
                status = "Under Budget"
                status_color = "success"

            total_budget += b.amount
            total_spent += spent

            items.append({
                "id": b.id,
                "category_id": b.category_id,
                "category_name": b.category.name if b.category else "Unknown",
                "category_color": b.category.color if b.category else "#6c757d",
                "amount": b.amount,
                "spent": spent,
                "remaining": remaining,
                "percentage": round(pct, 1),
                "status": status,
                "status_color": status_color,
            })

        overall_pct = (total_spent / total_budget * 100.0) if total_budget > 0 else 0.0

        return {
            "month": month,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_budget - total_spent,
            "overall_percentage": round(overall_pct, 1),
            "budgets": items,
        }
