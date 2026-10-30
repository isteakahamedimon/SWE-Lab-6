# ExpenseTrack - Personal Expense Tracker

A modular, production-ready Personal Expense Tracker web application built with **Python 3**, **Flask**, **SQLite**, **SQLAlchemy**, and **Bootstrap 5**.

---

## Table of Contents
- [Features](#features)
- [Architecture & Layered Design](#architecture--layered-design)
- [Design Patterns Implemented (GoF)](#design-patterns-implemented-gof)
  - [1. Factory Pattern (Creational)](#1-factory-pattern-creational)
  - [2. Adapter Pattern (Structural)](#2-adapter-pattern-structural)
  - [3. Observer Pattern (Behavioral)](#3-observer-pattern-behavioral)
- [Security & Validation](#security--validation)
- [Project Directory Structure](#project-directory-structure)
- [Installation & Local Setup](#installation--local-setup)
- [Running the Application](#running-the-application)
- [CSV Export Usage](#csv-export-usage)
- [Running Tests](#running-tests)
  - [Unit and Integration Tests](#unit-and-integration-tests)
  - [Mocking Examples (`unittest.mock`)](#mocking-examples-unittestmock)
  - [Selenium Browser Testing](#selenium-browser-testing)
  - [Test Coverage](#test-coverage)
- [Automated CI/CD (GitHub Actions)](#automated-cicd-github-actions)

---

## Features

1. **User Authentication & Session Management**:
   - Secure registration, login, and logout.
   - Industry-standard password hashing via `werkzeug.security`.
   - Automatic seeding of default income and expense categories upon new user registration.
   - Route protection with custom `@login_required` decorator.

2. **Category Management**:
   - Create, edit, and delete income and expense categories.
   - Customizable color tags for UI badges and visualizations.
   - Referential integrity: prevents accidental deletion of categories that have existing transactions attached.

3. **Transaction Management**:
   - Add, edit, delete, and view income and expense transactions.
   - Fields: Amount, Category, Date, Type (`income` / `expense`), Description/Notes.
   - Real-time client-side category filtering according to transaction type.

4. **Budget Management & Overspending Warnings**:
   - Set monthly spending targets per category (e.g., `2026-10`).
   - Visual progress bars dynamically reflecting budget usage.
   - Tiered status indicators:
     - `Under Budget` (< 80%)
     - `Warning` (80% - 99%)
     - `Exceeded` (>= 100%)

5. **Financial Dashboard & Analytics**:
   - High-level metric cards: Total Income, Total Expenses, Net Balance, and Current Month Spending.
   - Category-wise expense breakdown with relative percentage shares.
   - Multi-month cash flow history and savings rate analytics.
   - Interactive notification bell dropdown for budget alert updates.

6. **Search, Filtering, Import & Export**:
   - Filter transactions by date range (From Date / To Date), transaction type, category, and text keyword.
   - Sort transactions by date or amount in ascending or descending order.
   - One-click CSV export of transaction history.
   - CSV statement import supporting multiple external bank and spreadsheet formats.

---

## Architecture & Layered Design

ExpenseTrack strictly enforces a **modular, layered architecture** that cleanly separates concerns across the application:

```
[ HTTP Requests / Browser ]
           │
           ▼
[ Routes Layer (app/routes/) ] ──────────────► [ Forms & CSRF (app/forms/) ]
           │
           ▼
[ Services Layer (app/services/) ] ──────────► [ Design Patterns (app/patterns/) ]
           │                                    • Factory (Reports, Payloads)
           ▼                                    • Adapter (CSV Ingestion / Export)
[ Repositories Layer (app/repositories/) ]      • Observer (Budget Monitor, Audit)
           │
           ▼
[ Models & DB Layer (app/models/ & database.py) ]
           │
           ▼
      [ SQLite ]
```

- **Routes (`app/routes/`)**: Handles HTTP requests, session validation, form submission flow, and template rendering.
- **Forms (`app/forms/`)**: Implements WTForms with CSRF protection, input validation rules, and custom error messaging.
- **Services (`app/services/`)**: Orchestrates business logic, domain rules, pattern dispatching, and transaction workflows.
- **Repositories (`app/repositories/`)**: Encapsulates raw database queries and persistence using SQLAlchemy.
- **Models (`app/models/`)**: Defines database schemas, constraints, relationships, and model helper methods.
- **Design Patterns (`app/patterns/`)**: Provides decoupled, extensible domain components.

---

## Design Patterns Implemented (GoF)

The application genuinely implements **three GoF design patterns** spanning two categories:

### 1. Factory Pattern (Creational)
- **Implementation**: [`ReportFactory`](app/patterns/factory/report_factory.py) and [`TransactionFactory`](app/patterns/factory/transaction_factory.py)
- **Role**:
  - `ReportFactory` instantiates specialized `FinancialReport` objects based on the requested report key:
    - `MonthlySummaryReport`: Calculates monthly cash flows, net balances, and savings rates.
    - `CategoryBreakdownReport`: Computes category share and distribution percentages.
    - `BudgetPerformanceReport`: Computes budget variance, utilization percentages, and status alerts.
  - `TransactionFactory` constructs validated transaction creation payloads enforcing invariant constraints (positive amount, date validity, normalized type).

### 2. Adapter Pattern (Structural)
- **Implementation**: [`TransactionImportAdapter`](app/patterns/adapter/csv_adapter.py)
- **Role**: External institutions and exports format transaction data differently. The adapter pattern allows ExpenseTrack to ingest disparate external formats into standard domain transaction records:
  - `SimpleCSVAdapter`: Adapts CSV files with headers `Date, Type, Category, Amount, Description`.
  - `BankStatementCSVAdapter`: Adapts financial institution bank exports with debit/credit columns (`Date, Details, Debit, Credit`), converting debits to expenses and credits to income.
  - `CSVExportAdapter`: Adapts internal SQLAlchemy `Transaction` domain entities into downloadable CSV data.

### 3. Observer Pattern (Behavioral)
- **Implementation**: [`TransactionSubject`](app/patterns/observer/subject.py), [`BudgetAlertObserver`](app/patterns/observer/budget_observer.py), and [`AuditLogObserver`](app/patterns/observer/audit_observer.py)
- **Role**:
  - When a transaction is created, updated, or removed, `TransactionService` notifies attached observers through `TransactionSubject.notify(event, transaction)`.
  - `BudgetAlertObserver` automatically inspects whether category spending for that month has crossed the 80% warning threshold or 100% budget exceeded limit, creating user notification alerts in real-time.
  - `AuditLogObserver` logs transaction mutations for tracking and auditing.

---

## Security & Validation

- **Password Hashing**: Uses Werkzeug's secure PBKDF2 with SHA-256 password hashing. Passwords are never stored in plaintext.
- **CSRF Protection**: Comprehensive Flask-WTF CSRF protection enabled across all forms, deletes, and state-modifying requests.
- **Input Validation**: WTForms validators ensure type correctness, string lengths, positive amounts, valid date formats, and email standards.
- **Access Control**: Session-based user isolation. Database queries in repositories and services are strictly scoped to the logged-in `user_id`.

---

## Project Directory Structure

```text
ExpenseTrack/
├── .github/
│   └── workflows/
│       └── pytest.yml           # Automated CI workflow
├── app/
│   ├── __init__.py              # Application factory (create_app)
│   ├── config.py                # Environment and test configurations
│   ├── database.py              # SQLAlchemy database instance
│   ├── forms/                   # Flask-WTF form classes
│   │   ├── auth_forms.py
│   │   ├── category_forms.py
│   │   ├── transaction_forms.py
│   │   └── budget_forms.py
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   └── notification.py
│   ├── patterns/                # Design Pattern implementations
│   │   ├── factory/             # Factory (Creational)
│   │   ├── adapter/             # Adapter (Structural)
│   │   └── observer/            # Observer (Behavioral)
│   ├── repositories/            # Data access and query layer
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── category_repository.py
│   │   ├── transaction_repository.py
│   │   ├── budget_repository.py
│   │   └── notification_repository.py
│   ├── routes/                  # Blueprint controllers
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── categories.py
│   │   ├── transactions.py
│   │   ├── budgets.py
│   │   └── reports.py
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py
│   │   ├── category_service.py
│   │   ├── transaction_service.py
│   │   ├── budget_service.py
│   │   └── report_service.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html
│       ├── auth/
│       ├── dashboard/
│       ├── transactions/
│       ├── categories/
│       ├── budgets/
│       └── reports/
├── tests/
│   ├── conftest.py              # Pytest fixtures and app configurations
│   ├── test_models.py           # Unit tests for domain models
│   ├── test_repositories.py     # Unit tests for repository queries
│   ├── test_patterns.py         # Unit tests for Factory, Adapter, Observer
│   ├── test_services.py         # Unit tests for service layer
│   ├── test_mock_examples.py    # unittest.mock demonstrations
│   ├── test_routes.py           # Integration tests for routes & CSRF
│   └── test_selenium.py         # End-to-end browser automation suite
├── requirements.txt             # Project dependencies
├── run.py                       # Application execution entry point
├── README.md                    # Project documentation
└── .gitignore
```

---

## Installation & Local Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13, 3.14)
- `pip` package manager

### 2. Clone the Repository
```bash
git clone <repository-url>
cd "Lab 6"
```

### 3. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the Flask development server:
```bash
python3 run.py
```

The application will be live at:
```
http://127.0.0.1:5000/
```

- Navigate to `http://127.0.0.1:5000/register` to create a new user account.
- The system will immediately seed default income and expense categories (Salary, Freelance, Groceries, Rent, Utilities, Transport, etc.).
- Add your income and expenses, configure monthly budgets, and view reports.

---

## CSV Export Usage

### 1. Overview
The CSV export feature allows authenticated users to download their recorded financial transactions as a standard Comma-Separated Values (`.csv`) file for spreadsheets, accounting, or backup. The export transforms internal database models into tabular text using the [`CSVExportAdapter`](app/patterns/adapter/csv_adapter.py#L108-L130).

### 2. How to Access and Use
Users can download their CSV file directly from the web interface:
- **From the Transactions Page**: Navigate to **Transactions** (`/transactions/`) and click the **Export** button in the top action toolbar. If filters are active (e.g. filtered by transaction type), the export link preserves the `type` query parameter to export only the matching subset.
- **From the Dashboard**: Click the **Export Transactions (CSV)** link within the **Quick Tools** card on the right sidebar.

### 3. Route & Endpoint
- **URL**: `GET /transactions/export`
- **Controller**: `export_csv()` in [`app/routes/transactions.py`](app/routes/transactions.py#L164-L177)
- **Access Control**: Requires authentication (`@login_required`). Data is strictly scoped to the logged-in user.
- **Query Parameters**:
  - `type` *(optional)*: Filter by transaction type (`income` or `expense`). Omit to export all transactions.
- **Response**: Generates a `text/csv` attachment named `expensetrack_export_<YYYY-MM-DD>.csv`.

### 4. Exported File Schema
The exported CSV file contains a header row followed by one row per transaction:

| Column | Type | Description |
|---|---|---|
| `ID` | Integer | Unique identifier of the transaction record |
| `Date` | String | Transaction date formatted in ISO 8601 (`YYYY-MM-DD`) |
| `Type` | String | Transaction type (`income` or `expense`) |
| `Category` | String | Name of the assigned category (e.g., `Food & Groceries`, `Salary`) |
| `Amount` | Decimal | Monetary value formatted with 2 decimal places (e.g., `45.50`) |
| `Description` | String | Note or description entered for the transaction |

---

## Running Tests

The test suite contains 44 test cases covering models, repositories, business logic, design patterns, integration routes, and mocking examples.

### 1. Run All Tests
```bash
pytest -v
```

### 2. Run with Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

### 3. Run Mocking Demonstration Tests
ExpenseTrack demonstrates comprehensive usage of `unittest.mock` (`MagicMock`, `patch`) in [`tests/test_mock_examples.py`](tests/test_mock_examples.py):
```bash
pytest tests/test_mock_examples.py -v
```

### 4. Run Selenium Browser Tests
The project is fully prepared for browser testing via Selenium WebDriver in [`tests/test_selenium.py`](tests/test_selenium.py).

When Google Chrome / Chromium and `chromedriver` are installed on the system:
```bash
pytest tests/test_selenium.py -v
```
*(Note: If Chrome is not installed on the host runner, the test gracefully skips with a descriptive notice rather than failing).*

---

## Automated CI/CD (GitHub Actions)

An automated GitHub Actions workflow is provided at [`.github/workflows/pytest.yml`](.github/workflows/pytest.yml).

On every push or pull request to `main` or `master`, the workflow:
1. Sets up Python environments across multiple versions (`3.11`, `3.12`, `3.13`).
2. Installs dependencies from `requirements.txt`.
3. Runs the entire `pytest` test suite with code coverage analysis.
