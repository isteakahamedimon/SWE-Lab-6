import pytest
from datetime import date
from app import create_app
from app.config import TestConfig
from app.database import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.services.auth_service import AuthService


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()
            db.session.remove()
            db.engine.dispose()


@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        try:
            yield
        finally:
            db.session.remove()


@pytest.fixture
def client(app):
    try:
        yield app.test_client()
    finally:
        db.session.remove()


@pytest.fixture
def test_user(app):
    auth_service = AuthService()
    user, _ = auth_service.register_user(
        username="testuser",
        email="testuser@example.com",
        password="password123",
    )
    try:
        yield user
    finally:
        db.session.remove()


@pytest.fixture
def auth_client(client, test_user):
    with client.session_transaction() as sess:
        sess["user_id"] = test_user.id
        sess["username"] = test_user.username
    try:
        yield client
    finally:
        db.session.remove()


@pytest.fixture
def sample_data(app, test_user):
    user = db.session.get(User, test_user.id)
    food_cat = Category.query.filter_by(user_id=user.id, name="Food & Groceries").first()
    salary_cat = Category.query.filter_by(user_id=user.id, name="Salary").first()

    # Add income transaction
    t1 = Transaction(
        amount=3000.0,
        type="income",
        category_id=salary_cat.id,
        user_id=user.id,
        date=date.today(),
        description="Monthly salary",
    )
    # Add expense transaction
    t2 = Transaction(
        amount=150.0,
        type="expense",
        category_id=food_cat.id,
        user_id=user.id,
        date=date.today(),
        description="Grocery run",
    )
    # Add budget for current month
    b1 = Budget(
        category_id=food_cat.id,
        user_id=user.id,
        month=date.today().strftime("%Y-%m"),
        amount=500.0,
    )
    db.session.add_all([t1, t2, b1])
    db.session.commit()
    data = {
        "user_id": user.id,
        "food_cat_id": food_cat.id,
        "salary_cat_id": salary_cat.id,
        "income_tx_id": t1.id,
        "expense_tx_id": t2.id,
        "budget_id": b1.id,
    }
    try:
        yield data
    finally:
        db.session.rollback()
        db.session.remove()
