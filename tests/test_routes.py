import io
from datetime import date
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.database import db


# ---------------- Auth Route Tests ----------------

def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign In to ExpenseTrack" in response.data


def test_register_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create an Account" in response.data


def test_user_registration_route(client, app):
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful" in response.data


def test_user_login_logout_route(client, test_user):
    # Login
    response = client.post(
        "/login",
        data={
            "username_or_email": test_user.username,
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Financial Overview" in response.data

    # Logout
    logout_resp = client.post("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"You have been successfully logged out" in logout_resp.data


def test_protected_routes_redirect_unauthenticated(client):
    endpoints = ["/dashboard", "/transactions/", "/categories/", "/budgets/", "/reports/"]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------- Dashboard Route Tests ----------------

def test_dashboard_route(auth_client, sample_data):
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Financial Overview" in response.data
    assert b"Total Income" in response.data
    assert b"3000.00" in response.data
    assert b"150.00" in response.data


def test_mark_notifications_read(auth_client):
    response = auth_client.post("/notifications/mark-read", follow_redirects=True)
    assert response.status_code == 200


# ---------------- Categories Route Tests ----------------

def test_categories_index(auth_client):
    response = auth_client.get("/categories/")
    assert response.status_code == 200
    assert b"Income Categories" in response.data
    assert b"Expense Categories" in response.data


def test_category_create_and_edit(auth_client, app, test_user):
    # Create category
    create_resp = auth_client.post(
        "/categories/new",
        data={"name": "Freelance Dev", "type": "income", "color": "#123456"},
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert b"Freelance Dev" in create_resp.data

    with app.app_context():
        cat = Category.query.filter_by(name="Freelance Dev", user_id=test_user.id).first()
        cat_id = cat.id

    # Edit category
    edit_resp = auth_client.post(
        f"/categories/{cat_id}/edit",
        data={"name": "Freelance Coding", "type": "income", "color": "#654321"},
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200
    assert b"Freelance Coding" in edit_resp.data

    # Delete category
    del_resp = auth_client.post(f"/categories/{cat_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    assert b"Category deleted successfully" in del_resp.data


# ---------------- Transactions Route Tests ----------------

def test_transactions_index_and_filters(auth_client, sample_data):
    response = auth_client.get("/transactions/")
    assert response.status_code == 200
    assert b"Monthly salary" in response.data
    assert b"Grocery run" in response.data

    # Filter by type expense
    filtered_resp = auth_client.get("/transactions/?type=expense")
    assert filtered_resp.status_code == 200
    assert b"Grocery run" in filtered_resp.data
    assert b"Monthly salary" not in filtered_resp.data


def test_transaction_create_edit_delete(auth_client, app, test_user):
    with app.app_context():
        cat = Category.query.filter_by(user_id=test_user.id, type="expense").first()
        cat_id = cat.id

    # Create transaction
    create_resp = auth_client.post(
        "/transactions/new",
        data={
            "amount": "45.00",
            "type": "expense",
            "category_id": cat_id,
            "date": date.today().isoformat(),
            "description": "Lunch with teammates",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert b"Transaction added successfully" in create_resp.data
    assert b"Lunch with teammates" in create_resp.data

    with app.app_context():
        tx = Transaction.query.filter_by(description="Lunch with teammates").first()
        tx_id = tx.id

    # Edit transaction
    edit_resp = auth_client.post(
        f"/transactions/{tx_id}/edit",
        data={
            "amount": "50.00",
            "type": "expense",
            "category_id": cat_id,
            "date": date.today().isoformat(),
            "description": "Lunch with teammates and dessert",
        },
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200
    assert b"Transaction updated successfully" in edit_resp.data
    assert b"50.00" in edit_resp.data

    # Delete transaction
    del_resp = auth_client.post(f"/transactions/{tx_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    assert b"Transaction deleted successfully" in del_resp.data


def test_transactions_csv_export(auth_client, sample_data):
    response = auth_client.get("/transactions/export")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"Monthly salary" in response.data


def test_transactions_csv_import(auth_client):
    csv_content = b"Date,Type,Category,Amount,Description\n2026-10-14,expense,Groceries,42.50,Imported grocery\n"
    data = {
        "file": (io.BytesIO(csv_content), "test_import.csv"),
        "adapter_type": "simple",
    }
    response = auth_client.post(
        "/transactions/import",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Successfully imported 1 transaction(s)" in response.data


# ---------------- Budgets Route Tests ----------------

def test_budgets_routes(auth_client, app, test_user):
    with app.app_context():
        cat = Category.query.filter_by(user_id=test_user.id, type="expense").first()
        cat_id = cat.id

    # Create budget
    create_resp = auth_client.post(
        "/budgets/new",
        data={
            "category_id": cat_id,
            "month": "2026-11",
            "amount": "600.00",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert b"Budget saved successfully" in create_resp.data

    with app.app_context():
        b = Budget.query.filter_by(user_id=test_user.id, month="2026-11").first()
        b_id = b.id

    # Edit budget
    edit_resp = auth_client.post(
        f"/budgets/{b_id}/edit",
        data={
            "category_id": cat_id,
            "month": "2026-11",
            "amount": "750.00",
        },
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200
    assert b"Budget updated successfully" in edit_resp.data

    # Delete budget
    del_resp = auth_client.post(f"/budgets/{b_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    assert b"Budget deleted successfully" in del_resp.data


# ---------------- Reports Route Tests ----------------

def test_reports_page_routes(auth_client, sample_data):
    # Monthly Summary Report
    resp1 = auth_client.get("/reports/?type=monthly_summary")
    assert resp1.status_code == 200
    assert b"Monthly Cash Flow &amp; Savings Summary" in resp1.data or b"Monthly Cash Flow" in resp1.data

    # Category Breakdown Report
    resp2 = auth_client.get("/reports/?type=category_breakdown&cat_type=expense")
    assert resp2.status_code == 200
    assert b"Category Breakdown" in resp2.data

    # Budget Performance Report
    curr_month = date.today().strftime("%Y-%m")
    resp3 = auth_client.get(f"/reports/?type=budget_performance&month={curr_month}")
    assert resp3.status_code == 200
    assert b"Budget Performance" in resp3.data
