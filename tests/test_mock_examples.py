from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.report_service import ReportService
from app.patterns.observer.budget_observer import BudgetAlertObserver
from app.models.category import Category
from app.models.transaction import Transaction


def test_mock_category_service_delete_with_transactions():
    """
    Demonstrates unittest.mock.MagicMock:
    Mocking CategoryRepository to test category deletion prevention
    when transactions are linked to the category.
    """
    mock_category_repo = MagicMock()
    mock_category = MagicMock(spec=Category)
    mock_category.user_id = 1
    mock_category.transactions.count.return_value = 5  # 5 associated transactions

    mock_category_repo.get_by_id.return_value = mock_category

    service = CategoryService(category_repo=mock_category_repo)
    success, error = service.delete_category(category_id=10, user_id=1)

    assert success is False
    assert "Cannot delete category with associated transactions" in error
    mock_category_repo.delete.assert_not_called()


def test_mock_budget_alert_observer_danger():
    """
    Demonstrates mocking collaborating repositories in BudgetAlertObserver.
    Verifies that when spending >= 100% of budget, notification_repo.create() is called with 'danger'.
    """
    mock_budget_repo = MagicMock()
    mock_transaction_repo = MagicMock()
    mock_notification_repo = MagicMock()

    observer = BudgetAlertObserver(
        budget_repo=mock_budget_repo,
        transaction_repo=mock_transaction_repo,
        notification_repo=mock_notification_repo,
    )

    # Mock budget of $200
    mock_budget = MagicMock()
    mock_budget.amount = 200.0
    mock_budget_repo.get_by_category_and_month.return_value = mock_budget

    # Mock spent = $220 (> 100%)
    mock_transaction_repo.get_expense_by_category_for_month.return_value = 220.0

    # Create dummy transaction
    mock_tx = MagicMock()
    mock_tx.type = "expense"
    mock_tx.amount = 50.0
    mock_tx.user_id = 7
    mock_tx.category_id = 3
    mock_tx.date = date(2026, 10, 20)
    mock_tx.category.name = "Dining Out"

    observer.on_transaction_event("created", mock_tx)

    mock_notification_repo.create.assert_called_once()
    call_kwargs = mock_notification_repo.create.call_args.kwargs
    assert call_kwargs["user_id"] == 7
    assert call_kwargs["level"] == "danger"
    assert "Budget Exceeded!" in call_kwargs["title"]


def test_mock_budget_alert_observer_warning():
    """
    Demonstrates verifying warning threshold (80% - 99%) in BudgetAlertObserver.
    """
    mock_budget_repo = MagicMock()
    mock_transaction_repo = MagicMock()
    mock_notification_repo = MagicMock()

    observer = BudgetAlertObserver(
        budget_repo=mock_budget_repo,
        transaction_repo=mock_transaction_repo,
        notification_repo=mock_notification_repo,
    )

    mock_budget = MagicMock()
    mock_budget.amount = 100.0
    mock_budget_repo.get_by_category_and_month.return_value = mock_budget

    # Mock spent = $85 (85%)
    mock_transaction_repo.get_expense_by_category_for_month.return_value = 85.0

    mock_tx = MagicMock()
    mock_tx.type = "expense"
    mock_tx.amount = 20.0
    mock_tx.user_id = 7
    mock_tx.category_id = 3
    mock_tx.date = date(2026, 10, 20)
    mock_tx.category.name = "Groceries"

    observer.on_transaction_event("created", mock_tx)

    mock_notification_repo.create.assert_called_once()
    call_kwargs = mock_notification_repo.create.call_args.kwargs
    assert call_kwargs["level"] == "warning"
    assert "Budget Warning" in call_kwargs["title"]


def test_mock_transaction_service_import_adapter():
    """
    Demonstrates unittest.mock.patch to mock CSV Adapter parsing during transaction import.
    """
    mock_tx_repo = MagicMock()
    mock_cat_repo = MagicMock()
    mock_subject = MagicMock()

    service = TransactionService(
        transaction_repo=mock_tx_repo,
        category_repo=mock_cat_repo,
        subject=mock_subject,
    )

    # Mock existing category
    mock_cat = MagicMock()
    mock_cat.id = 99
    mock_cat_repo.get_by_id.return_value = mock_cat
    mock_cat.user_id = 1
    mock_cat.type = "expense"
    mock_cat_repo.get_by_name_and_user.return_value = mock_cat

    mock_tx_repo.create.return_value = MagicMock(spec=Transaction)

    fake_parsed_records = [
        {
            "date": date(2026, 10, 1),
            "type": "expense",
            "category_name": "Utilities",
            "amount": 75.0,
            "description": "Electric bill",
        }
    ]

    with patch("app.services.transaction_service.SimpleCSVAdapter") as MockAdapterClass:
        mock_adapter_instance = MockAdapterClass.return_value
        mock_adapter_instance.parse.return_value = fake_parsed_records

        count, errors = service.import_transactions(
            user_id=1, content="mock_csv_content", adapter_type="simple"
        )

        assert count == 1
        assert len(errors) == 0
        mock_adapter_instance.parse.assert_called_once_with("mock_csv_content")
        mock_tx_repo.create.assert_called_once()


def test_mock_report_service_factory_delegation():
    """
    Demonstrates unittest.mock.patch:
    Mocking ReportFactory to ensure ReportService properly delegates report generation.
    """
    mock_tx_repo = MagicMock()
    mock_b_repo = MagicMock()
    mock_n_repo = MagicMock()

    service = ReportService(
        transaction_repo=mock_tx_repo,
        budget_repo=mock_b_repo,
        notification_repo=mock_n_repo,
    )

    with patch("app.services.report_service.ReportFactory.create_report") as mock_create_report:
        mock_report_instance = MagicMock()
        mock_report_instance.generate.return_value = {"type": "mock_report", "status": "ok"}
        mock_create_report.return_value = mock_report_instance

        result = service.generate_report("monthly_summary", user_id=123, custom_arg="val")

        mock_create_report.assert_called_once_with("monthly_summary")
        mock_report_instance.generate.assert_called_once()
        assert result == {"type": "mock_report", "status": "ok"}
