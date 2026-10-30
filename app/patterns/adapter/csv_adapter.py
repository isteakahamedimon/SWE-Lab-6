import csv
import io
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Dict, Any


class TransactionImportAdapter(ABC):
    """
    Target interface for adapting various tabular/file sources into
    standard transaction dictionaries understood by TransactionService.
    Expected dict structure:
    {
        'date': date,
        'type': 'income' | 'expense',
        'category_name': str,
        'amount': float,
        'description': str
    }
    """

    @abstractmethod
    def parse(self, content_stream: str) -> List[Dict[str, Any]]:
        pass


class SimpleCSVAdapter(TransactionImportAdapter):
    """
    Adapts CSV with headers: Date, Type, Category, Amount, Description
    """

    def parse(self, content_stream: str) -> List[Dict[str, Any]]:
        f = io.StringIO(content_stream.strip())
        reader = csv.DictReader(f)
        records = []

        for row in reader:
            normalized_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            date_str = normalized_row.get("date", "")
            t_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            t_type = normalized_row.get("type", "expense").lower()
            if t_type not in ("income", "expense"):
                t_type = "expense"

            amount = float(normalized_row.get("amount", 0.0))
            category_name = normalized_row.get("category", "General")
            description = normalized_row.get("description", "")

            records.append({
                "date": t_date,
                "type": t_type,
                "category_name": category_name,
                "amount": amount,
                "description": description,
            })

        return records


class BankStatementCSVAdapter(TransactionImportAdapter):
    """
    Adapts standard bank export with headers: Date, Details, Debit, Credit
    Debit represents an expense, Credit represents an income.
    """

    def parse(self, content_stream: str) -> List[Dict[str, Any]]:
        f = io.StringIO(content_stream.strip())
        reader = csv.DictReader(f)
        records = []

        for row in reader:
            normalized_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            date_str = normalized_row.get("date", "")
            # Support both YYYY-MM-DD and MM/DD/YYYY formats
            try:
                t_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                t_date = datetime.strptime(date_str, "%m/%d/%Y").date()

            details = normalized_row.get("details", "") or normalized_row.get("description", "")
            debit_str = normalized_row.get("debit", "")
            credit_str = normalized_row.get("credit", "")

            debit = float(debit_str) if debit_str else 0.0
            credit = float(credit_str) if credit_str else 0.0

            if debit > 0:
                records.append({
                    "date": t_date,
                    "type": "expense",
                    "category_name": normalized_row.get("category", "General Expense"),
                    "amount": debit,
                    "description": details,
                })
            elif credit > 0:
                records.append({
                    "date": t_date,
                    "type": "income",
                    "category_name": normalized_row.get("category", "General Income"),
                    "amount": credit,
                    "description": details,
                })

        return records


class CSVExportAdapter:
    """
    Adapter converting internal Transaction models into standard CSV string.
    """

    @staticmethod
    def export(transactions: List[Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Date", "Type", "Category", "Amount", "Description"])

        for t in transactions:
            cat_name = t.category.name if getattr(t, "category", None) else ""
            writer.writerow([
                t.id,
                t.date.isoformat() if t.date else "",
                t.type,
                cat_name,
                f"{t.amount:.2f}",
                t.description or "",
            ])

        return output.getvalue()
