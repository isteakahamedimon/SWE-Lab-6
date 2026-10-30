from datetime import date
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.notification_repository import NotificationRepository


def test_user_repository_crud(app):
    repo = UserRepository()
    user = repo.create(username="bob", email="bob@example.com", password="password123")
    assert user.id is not None
    assert repo.get_by_username("bob") == user
    assert repo.get_by_email("bob@example.com") == user
    assert repo.get_by_id(user.id) == user


def test_category_repository(app, test_user):
    repo = CategoryRepository()
    cat = repo.create(name="Crypto", type_="income", user_id=test_user.id, color="#00ff00")
    assert cat.id is not None

    found = repo.get_by_name_and_user("Crypto", test_user.id, type_="income")
    assert found == cat

    incomes = repo.get_by_user_and_type(test_user.id, "income")
    assert any(c.name == "Crypto" for c in incomes)


def test_transaction_repository_queries(app, test_user, sample_data):
    repo = TransactionRepository()

    # Get by user
    txs = repo.get_by_user(test_user.id)
    assert len(txs) >= 2

    # Filter by type
    expenses = repo.filter_transactions(user_id=test_user.id, type_="expense")
    assert len(expenses) == 1
    assert expenses[0].amount == 150.0

    # User totals
    totals = repo.get_user_totals(test_user.id)
    assert totals["income"] == 3000.0
    assert totals["expense"] == 150.0
    assert totals["balance"] == 2850.0

    # Monthly totals
    curr_month = date.today().strftime("%Y-%m")
    m_totals = repo.get_monthly_totals_for_user(test_user.id, curr_month)
    assert m_totals["income"] == 3000.0
    assert m_totals["expense"] == 150.0

    # Category expense
    spent = repo.get_expense_by_category_for_month(
        test_user.id, sample_data["food_cat_id"], curr_month
    )
    assert spent == 150.0

    # Monthly summary list
    summary = repo.get_monthly_summary(test_user.id)
    assert len(summary) >= 1
    assert summary[0]["income"] == 3000.0

    # Category breakdown
    breakdown = repo.get_category_breakdown(test_user.id, type_="expense")
    assert len(breakdown) >= 1
    assert breakdown[0]["total"] == 150.0


def test_budget_repository(app, test_user, sample_data):
    repo = BudgetRepository()
    curr_month = date.today().strftime("%Y-%m")

    budget = repo.get_by_category_and_month(
        test_user.id, sample_data["food_cat_id"], curr_month
    )
    assert budget is not None
    assert budget.amount == 500.0

    budgets = repo.get_by_user_and_month(test_user.id, curr_month)
    assert len(budgets) == 1


def test_notification_repository(app, test_user):
    repo = NotificationRepository()
    n = repo.create(
        user_id=test_user.id,
        title="Test Alert",
        message="This is a test notification",
        level="warning",
    )
    assert n.id is not None
    assert n.is_read is False

    unread = repo.get_by_user(test_user.id, unread_only=True)
    assert len(unread) >= 1

    repo.mark_all_as_read(test_user.id)
    unread_after = repo.get_by_user(test_user.id, unread_only=True)
    assert len(unread_after) == 0
