from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from sqlalchemy import func
from app.database import db
from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    def get_by_user(self, user_id: int) -> List[Transaction]:
        return (
            Transaction.query.filter_by(user_id=user_id)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .all()
        )

    def filter_transactions(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        type_: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> List[Transaction]:
        query = Transaction.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        if type_ and type_ in ("income", "expense"):
            query = query.filter(Transaction.type == type_)
        if keyword:
            term = f"%{keyword.strip()}%"
            query = query.filter(Transaction.description.ilike(term))

        order_col = Transaction.amount if sort_by == "amount" else Transaction.date
        if sort_order == "asc":
            query = query.order_by(order_col.asc(), Transaction.id.asc())
        else:
            query = query.order_by(order_col.desc(), Transaction.id.desc())

        return query.all()

    def get_user_totals(self, user_id: int) -> Dict[str, float]:
        rows = (
            db.session.query(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0.0).label("total"),
            )
            .filter(Transaction.user_id == user_id)
            .group_by(Transaction.type)
            .all()
        )
        totals = {"income": 0.0, "expense": 0.0}
        for type_, amount in rows:
            totals[type_] = float(amount)
        totals["balance"] = totals["income"] - totals["expense"]
        return totals

    def get_monthly_totals_for_user(
        self, user_id: int, month_str: str
    ) -> Dict[str, float]:
        """month_str format: 'YYYY-MM'"""
        start_d = date.fromisoformat(f"{month_str}-01")
        # determine next month start
        year = int(month_str[:4])
        month = int(month_str[5:7])
        if month == 12:
            next_start_d = date(year + 1, 1, 1)
        else:
            next_start_d = date(year, month + 1, 1)

        rows = (
            db.session.query(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0.0).label("total"),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_d,
                Transaction.date < next_start_d,
            )
            .group_by(Transaction.type)
            .all()
        )
        totals = {"income": 0.0, "expense": 0.0}
        for type_, amount in rows:
            totals[type_] = float(amount)
        totals["balance"] = totals["income"] - totals["expense"]
        return totals

    def get_expense_by_category_for_month(
        self, user_id: int, category_id: int, month_str: str
    ) -> float:
        start_d = date.fromisoformat(f"{month_str}-01")
        year = int(month_str[:4])
        month = int(month_str[5:7])
        if month == 12:
            next_start_d = date(year + 1, 1, 1)
        else:
            next_start_d = date(year, month + 1, 1)

        result = (
            db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.type == "expense",
                Transaction.date >= start_d,
                Transaction.date < next_start_d,
            )
            .scalar()
        )
        return float(result or 0.0)

    def get_monthly_summary(self, user_id: int, limit_months: int = 6) -> List[Dict[str, Any]]:
        """Returns monthly grouped income and expense summary list sorted chronologically."""
        # SQLite supports strftime('%Y-%m', date)
        month_label = func.strftime("%Y-%m", Transaction.date).label("month")
        results = (
            db.session.query(
                month_label,
                Transaction.type,
                func.sum(Transaction.amount).label("total"),
            )
            .filter(Transaction.user_id == user_id)
            .group_by(month_label, Transaction.type)
            .order_by(month_label.desc())
            .all()
        )

        month_map: Dict[str, Dict[str, float]] = {}
        for m, t, total in results:
            if m not in month_map:
                month_map[m] = {"month": m, "income": 0.0, "expense": 0.0, "balance": 0.0}
            month_map[m][t] = float(total)
            month_map[m]["balance"] = month_map[m]["income"] - month_map[m]["expense"]

        sorted_months = sorted(month_map.values(), key=lambda x: x["month"], reverse=True)
        return sorted_months[:limit_months]

    def get_category_breakdown(
        self, user_id: int, type_: str = "expense", month_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        from app.models.category import Category

        query = (
            db.session.query(
                Category.name,
                Category.color,
                func.sum(Transaction.amount).label("total"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .filter(Transaction.user_id == user_id, Transaction.type == type_)
        )

        if month_str:
            start_d = date.fromisoformat(f"{month_str}-01")
            year = int(month_str[:4])
            month = int(month_str[5:7])
            if month == 12:
                next_start_d = date(year + 1, 1, 1)
            else:
                next_start_d = date(year, month + 1, 1)
            query = query.filter(
                Transaction.date >= start_d, Transaction.date < next_start_d
            )

        rows = (
            query.group_by(Category.name, Category.color)
            .order_by(func.sum(Transaction.amount).desc())
            .all()
        )
        return [
            {"category": name, "color": color, "total": float(total)}
            for name, color, total in rows
        ]

    def create(
        self,
        amount: float,
        type_: str,
        category_id: int,
        user_id: int,
        date_: date,
        description: str = "",
    ) -> Transaction:
        transaction = Transaction(
            amount=amount,
            type=type_,
            category_id=category_id,
            user_id=user_id,
            date=date_,
            description=description,
        )
        return self.add(transaction)
