import pytest
from datetime import date
from app.patterns.factory.report_factory import (
    ReportFactory,
    MonthlySummaryReport,
    CategoryBreakdownReport,
    BudgetPerformanceReport,
)
from app.patterns.factory.transaction_factory import TransactionFactory
from app.patterns.adapter.csv_adapter import (
    SimpleCSVAdapter,
    BankStatementCSVAdapter,
    CSVExportAdapter,
)
from app.patterns.observer.subject import TransactionSubject, TransactionObserver
from app.patterns.observer.budget_observer import BudgetAlertObserver
from app.patterns.observer.audit_observer import AuditLogObserver
from app.models.transaction import Transaction
from app.models.category import Category


# ------------------ Factory Pattern Tests ------------------

def test_report_factory_instantiation():
    r1 = ReportFactory.create_report("monthly_summary")
    assert isinstance(r1, MonthlySummaryReport)

    r2 = ReportFactory.create_report("category_breakdown")
    assert isinstance(r2, CategoryBreakdownReport)

    r3 = ReportFactory.create_report("budget_performance")
    assert isinstance(r3, BudgetPerformanceReport)

    with pytest.raises(ValueError):
        ReportFactory.create_report("non_existent_report_type")


def test_transaction_factory_payload():
    payload = TransactionFactory.create_payload(
        amount=100.5,
        type_="EXPENSE",
        category_id=1,
        user_id=2,
        date_val=date(2026, 10, 1),
        description=" groceries ",
    )
    assert payload["amount"] == 100.5
    assert payload["type"] == "expense"
    assert payload["description"] == "groceries"

    with pytest.raises(ValueError):
        TransactionFactory.create_payload(
            amount=-50,
            type_="expense",
            category_id=1,
            user_id=2,
            date_val=date.today(),
        )

    with pytest.raises(ValueError):
        TransactionFactory.create_payload(
            amount=50,
            type_="invalid_type",
            category_id=1,
            user_id=2,
            date_val=date.today(),
        )


# ------------------ Adapter Pattern Tests ------------------

def test_simple_csv_adapter():
    adapter = SimpleCSVAdapter()
    csv_data = """Date,Type,Category,Amount,Description
2026-10-01,expense,Groceries,75.25,Weekly supermarket
2026-10-02,income,Salary,2500.00,Monthly pay
"""
    results = adapter.parse(csv_data)
    assert len(results) == 2
    assert results[0]["date"] == date(2026, 10, 1)
    assert results[0]["type"] == "expense"
    assert results[0]["amount"] == 75.25
    assert results[0]["category_name"] == "Groceries"

    assert results[1]["date"] == date(2026, 10, 2)
    assert results[1]["type"] == "income"
    assert results[1]["amount"] == 2500.00


def test_bank_statement_csv_adapter():
    adapter = BankStatementCSVAdapter()
    bank_csv = """Date,Details,Debit,Credit
2026-10-05,Coffee Shop,4.50,
2026-10-06,Client Payment,,600.00
"""
    results = adapter.parse(bank_csv)
    assert len(results) == 2
    assert results[0]["type"] == "expense"
    assert results[0]["amount"] == 4.50
    assert results[0]["description"] == "Coffee Shop"

    assert results[1]["type"] == "income"
    assert results[1]["amount"] == 600.00
    assert results[1]["description"] == "Client Payment"


def test_csv_export_adapter(app):
    cat = Category(id=1, name="Dining", type="expense", user_id=1)
    t1 = Transaction(
        id=1,
        date=date(2026, 10, 10),
        type="expense",
        amount=35.0,
        description="Dinner",
    )
    t1.category = cat

    exported = CSVExportAdapter.export([t1])
    assert "ID,Date,Type,Category,Amount,Description" in exported
    assert "1,2026-10-10,expense,Dining,35.00,Dinner" in exported



# ------------------ Observer Pattern Tests ------------------

class CustomTestObserver(TransactionObserver):
    def __init__(self):
        self.events = []

    def on_transaction_event(self, event_type: str, transaction) -> None:
        self.events.append((event_type, transaction))


def test_transaction_subject_notifications():
    subject = TransactionSubject()
    observer1 = CustomTestObserver()
    observer2 = CustomTestObserver()

    subject.attach(observer1)
    subject.attach(observer2)

    dummy_tx = Transaction(id=99, amount=50.0, type="expense")
    subject.notify("created", dummy_tx)

    assert len(observer1.events) == 1
    assert observer1.events[0] == ("created", dummy_tx)
    assert len(observer2.events) == 1

    subject.detach(observer1)
    subject.notify("deleted", dummy_tx)
    assert len(observer1.events) == 1  # Not updated
    assert len(observer2.events) == 2


def test_audit_log_observer():
    audit_observer = AuditLogObserver()
    dummy_tx = Transaction(id=1, amount=120.0, type="expense", user_id=42, date=date.today())

    audit_observer.on_transaction_event("created", dummy_tx)
    assert len(audit_observer.audit_log) == 1
    record = audit_observer.audit_log[0]
    assert record["event"] == "created"
    assert record["transaction_id"] == 1
    assert record["user_id"] == 42
