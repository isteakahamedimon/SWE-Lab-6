from datetime import date
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.budget_service import BudgetService
from app.services.report_service import ReportService


def test_auth_service_registration_and_auth(app):
    auth_service = AuthService()

    # Successful registration
    user, err = auth_service.register_user("charlie", "charlie@example.com", "pass123")
    assert err is None
    assert user is not None
    assert user.categories.count() > 0  # verifies default categories seeded

    # Duplicate username
    dup_user, dup_err = auth_service.register_user("charlie", "another@example.com", "pass123")
    assert dup_user is None
    assert "Username already exists" in dup_err

    # Duplicate email
    dup_email_user, dup_email_err = auth_service.register_user("charlie2", "charlie@example.com", "pass123")
    assert dup_email_user is None
    assert "Email address is already registered" in dup_email_err

    # Authentication
    auth_ok = auth_service.authenticate("charlie", "pass123")
    assert auth_ok is not None
    assert auth_ok.id == user.id

    # Authentication failure
    auth_fail = auth_service.authenticate("charlie", "wrong")
    assert auth_fail is None


def test_category_service(app, test_user):
    service = CategoryService()

    # Create category
    cat, err = service.create_category("Dividends", "income", test_user.id, "#112233")
    assert err is None
    assert cat.name == "Dividends"

    # Duplicate category
    _, dup_err = service.create_category("Dividends", "income", test_user.id)
    assert dup_err is not None

    # Update category
    updated, err = service.update_category(cat.id, test_user.id, "Stock Dividends", "income", "#334455")
    assert err is None
    assert updated.name == "Stock Dividends"

    # Delete category
    deleted, err = service.delete_category(cat.id, test_user.id)
    assert deleted is True
    assert err is None


def test_transaction_service(app, test_user):
    cat_service = CategoryService()
    tx_service = TransactionService()

    expense_cat = cat_service.get_user_categories(test_user.id, type_="expense")[0]

    # Create transaction
    tx, err = tx_service.create_transaction(
        amount=85.0,
        type_="expense",
        category_id=expense_cat.id,
        user_id=test_user.id,
        date_val=date.today(),
        description="Book purchase",
    )
    assert err is None
    assert tx.amount == 85.0

    # Retrieve transaction
    found = tx_service.get_transaction_by_id(tx.id, test_user.id)
    assert found == tx

    # Update transaction
    updated, err = tx_service.update_transaction(
        transaction_id=tx.id,
        user_id=test_user.id,
        amount=95.0,
        type_="expense",
        category_id=expense_cat.id,
        date_val=date.today(),
        description="Updated book purchase",
    )
    assert err is None
    assert updated.amount == 95.0

    # CSV Export
    csv_str = tx_service.export_transactions_csv(test_user.id)
    assert "Updated book purchase" in csv_str

    # Delete transaction
    deleted, err = tx_service.delete_transaction(tx.id, test_user.id)
    assert deleted is True
    assert tx_service.get_transaction_by_id(tx.id, test_user.id) is None


def test_budget_service(app, test_user):
    cat_service = CategoryService()
    b_service = BudgetService()

    expense_cat = cat_service.get_user_categories(test_user.id, type_="expense")[0]
    curr_month = date.today().strftime("%Y-%m")

    # Set budget
    budget, err = b_service.set_budget(
        user_id=test_user.id,
        category_id=expense_cat.id,
        month=curr_month,
        amount=300.0,
    )
    assert err is None
    assert budget.amount == 300.0

    # Overview
    overview = b_service.get_budget_overview(test_user.id, curr_month)
    assert overview["total_budget"] >= 300.0
    assert len(overview["budgets"]) >= 1

    # Update budget
    upd, err = b_service.update_budget(budget.id, test_user.id, 450.0)
    assert err is None
    assert upd.amount == 450.0

    # Delete budget
    deleted, err = b_service.delete_budget(budget.id, test_user.id)
    assert deleted is True


def test_report_service(app, test_user, sample_data):
    report_service = ReportService()
    curr_month = date.today().strftime("%Y-%m")

    # Dashboard summary
    summary = report_service.get_dashboard_summary(test_user.id)
    assert summary["all_time"]["income"] == 3000.0
    assert summary["all_time"]["expense"] == 150.0
    assert summary["all_time"]["balance"] == 2850.0
    assert len(summary["recent_transactions"]) >= 2

    # Factory Reports via Service
    monthly_report = report_service.generate_report("monthly_summary", test_user.id)
    assert monthly_report["type"] == "monthly_summary"

    category_report = report_service.generate_report("category_breakdown", test_user.id, type="expense")
    assert category_report["type"] == "category_breakdown"

    budget_report = report_service.generate_report("budget_performance", test_user.id, month=curr_month)
    assert budget_report["type"] == "budget_performance"
