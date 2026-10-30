from typing import List, Optional
from app.models.budget import Budget
from app.repositories.base_repository import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self):
        super().__init__(Budget)

    def get_by_user(self, user_id: int) -> List[Budget]:
        return (
            Budget.query.filter_by(user_id=user_id)
            .order_by(Budget.month.desc())
            .all()
        )

    def get_by_user_and_month(self, user_id: int, month: str) -> List[Budget]:
        return (
            Budget.query.filter_by(user_id=user_id, month=month)
            .order_by(Budget.id.asc())
            .all()
        )

    def get_by_category_and_month(
        self, user_id: int, category_id: int, month: str
    ) -> Optional[Budget]:
        return Budget.query.filter_by(
            user_id=user_id, category_id=category_id, month=month
        ).first()

    def create(
        self, user_id: int, category_id: int, month: str, amount: float
    ) -> Budget:
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            month=month,
            amount=amount,
        )
        return self.add(budget)
