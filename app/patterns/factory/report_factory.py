from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import date


class FinancialReport(ABC):
    @abstractmethod
    def generate(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report data dictionary."""
        pass


class MonthlySummaryReport(FinancialReport):
    """
    Report summarizing monthly trends: total income, expenses, net savings, and savings rate.
    """

    def generate(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        transaction_repo = context["transaction_repo"]
        limit = context.get("limit", 6)
        summaries = transaction_repo.get_monthly_summary(user_id, limit_months=limit)

        enhanced = []
        for s in summaries:
            inc = s["income"]
            exp = s["expense"]
            bal = inc - exp
            savings_rate = (bal / inc * 100.0) if inc > 0 else 0.0
            enhanced.append({
                "month": s["month"],
                "income": inc,
                "expense": exp,
                "balance": bal,
                "savings_rate": round(savings_rate, 1),
            })

        return {
            "type": "monthly_summary",
            "title": "Monthly Cash Flow & Savings Summary",
            "data": enhanced,
        }


class CategoryBreakdownReport(FinancialReport):
    """
    Report breaking down expenses or income by category, calculating percentage share.
    """

    def generate(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        transaction_repo = context["transaction_repo"]
        type_ = context.get("type", "expense")
        month = context.get("month", None)

        breakdown = transaction_repo.get_category_breakdown(
            user_id=user_id, type_=type_, month_str=month
        )
        total_sum = sum(b["total"] for b in breakdown)

        items = []
        for b in breakdown:
            pct = (b["total"] / total_sum * 100.0) if total_sum > 0 else 0.0
            items.append({
                "category": b["category"],
                "color": b["color"],
                "amount": b["total"],
                "percentage": round(pct, 1),
            })

        return {
            "type": "category_breakdown",
            "title": f"Category Breakdown ({type_.capitalize()})",
            "total": total_sum,
            "month": month or "All Time",
            "data": items,
        }


class BudgetPerformanceReport(FinancialReport):
    """
    Report analyzing budget performance for a given month:
    planned vs actual spending, remaining budget, and status (Under Budget, Warning, Exceeded).
    """

    def generate(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        budget_repo = context["budget_repo"]
        transaction_repo = context["transaction_repo"]
        month = context.get("month", date.today().strftime("%Y-%m"))

        budgets = budget_repo.get_by_user_and_month(user_id, month)
        results = []
        total_budgeted = 0.0
        total_spent = 0.0

        for b in budgets:
            spent = transaction_repo.get_expense_by_category_for_month(
                user_id, b.category_id, month
            )
            total_budgeted += b.amount
            total_spent += spent
            remaining = b.amount - spent
            pct = (spent / b.amount * 100.0) if b.amount > 0 else 0.0

            if pct >= 100.0:
                status = "Exceeded"
                status_class = "danger"
            elif pct >= 80.0:
                status = "Warning"
                status_class = "warning"
            else:
                status = "Under Budget"
                status_class = "success"

            results.append({
                "budget_id": b.id,
                "category_id": b.category_id,
                "category_name": b.category.name if b.category else "Unknown",
                "budgeted": b.amount,
                "spent": spent,
                "remaining": remaining,
                "percentage": round(pct, 1),
                "status": status,
                "status_class": status_class,
            })

        return {
            "type": "budget_performance",
            "title": f"Budget Performance for {month}",
            "month": month,
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "total_variance": total_budgeted - total_spent,
            "data": results,
        }


class ReportFactory:
    """
    Factory class providing instantiated reports according to the requested report type.
    """

    _registry = {
        "monthly_summary": MonthlySummaryReport,
        "category_breakdown": CategoryBreakdownReport,
        "budget_performance": BudgetPerformanceReport,
    }

    @classmethod
    def register_report(cls, report_type: str, report_cls):
        cls._registry[report_type] = report_cls

    @classmethod
    def create_report(cls, report_type: str) -> FinancialReport:
        report_cls = cls._registry.get(report_type)
        if not report_cls:
            raise ValueError(f"Unknown report type: '{report_type}'. Available: {list(cls._registry.keys())}")
        return report_cls()
