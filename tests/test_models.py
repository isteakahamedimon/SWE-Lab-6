from datetime import date
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.notification import Notification


def test_user_password_hashing(app):
    user = User(username="alice", email="alice@example.com")
    user.set_password("secret123")

    assert user.password_hash != "secret123"
    assert user.check_password("secret123") is True
    assert user.check_password("wrongpassword") is False
    assert "<User alice>" in repr(user)


def test_category_representation(app):
    cat = Category(name="Utilities", type="expense", user_id=1, color="#123456")
    assert "Utilities" in repr(cat)
    assert "expense" in repr(cat)


def test_transaction_to_dict(app):
    t = Transaction(
        amount=45.5,
        type="expense",
        category_id=1,
        user_id=1,
        date=date(2026, 10, 15),
        description="Coffee and snacks",
    )
    t_dict = t.to_dict()
    assert t_dict["amount"] == 45.5
    assert t_dict["type"] == "expense"
    assert t_dict["date"] == "2026-10-15"
    assert t_dict["description"] == "Coffee and snacks"
    assert "<Transaction expense 45.5" in repr(t)


def test_budget_representation(app):
    b = Budget(user_id=1, category_id=2, month="2026-10", amount=400.0)
    assert "2026-10" in repr(b)
    assert "400.0" in repr(b)


def test_notification_representation(app):
    notif = Notification(user_id=1, title="Over budget", message="Warning limit", level="danger")
    assert "Over budget" in repr(notif)
    assert "danger" in repr(notif)
