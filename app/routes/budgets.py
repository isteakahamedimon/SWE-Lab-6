from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from datetime import date
from app.routes.auth import login_required
from app.forms.budget_forms import BudgetForm
from app.services.budget_service import BudgetService
from app.services.category_service import CategoryService

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")
budget_service = BudgetService()
category_service = CategoryService()


@budgets_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    overview = budget_service.get_budget_overview(user_id=user_id, month=month)
    return render_template("budgets/index.html", overview=overview, selected_month=month)


@budgets_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    user_id = session["user_id"]
    form = BudgetForm()

    expense_cats = category_service.get_user_categories(user_id, type_="expense")
    if not expense_cats:
        flash("You need at least one expense category to set a budget.", "warning")
        return redirect(url_for("categories.new"))

    form.category_id.choices = [(c.id, c.name) for c in expense_cats]

    if form.validate_on_submit():
        budget, error = budget_service.set_budget(
            user_id=user_id,
            category_id=form.category_id.data,
            month=form.month.data,
            amount=float(form.amount.data),
        )
        if error:
            flash(error, "danger")
        else:
            flash("Budget saved successfully!", "success")
            return redirect(url_for("budgets.index", month=form.month.data))

    return render_template("budgets/form.html", form=form, title="Set Monthly Budget")


@budgets_bp.route("/<int:budget_id>/edit", methods=["GET", "POST"])
@login_required
def edit(budget_id: int):
    user_id = session["user_id"]
    budget = budget_service.get_budget_by_id(budget_id, user_id)
    if not budget:
        flash("Budget not found.", "danger")
        return redirect(url_for("budgets.index"))

    form = BudgetForm(obj=budget)
    expense_cats = category_service.get_user_categories(user_id, type_="expense")
    form.category_id.choices = [(c.id, c.name) for c in expense_cats]

    if form.validate_on_submit():
        updated, error = budget_service.set_budget(
            user_id=user_id,
            category_id=form.category_id.data,
            month=form.month.data,
            amount=float(form.amount.data),
        )
        if error:
            flash(error, "danger")
        else:
            flash("Budget updated successfully!", "success")
            return redirect(url_for("budgets.index", month=form.month.data))

    return render_template("budgets/form.html", form=form, title="Edit Monthly Budget", budget=budget)


@budgets_bp.route("/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete(budget_id: int):
    user_id = session["user_id"]
    budget = budget_service.get_budget_by_id(budget_id, user_id)
    target_month = budget.month if budget else None

    success, error = budget_service.delete_budget(budget_id, user_id)
    if success:
        flash("Budget deleted successfully.", "success")
    else:
        flash(error or "Failed to delete budget.", "danger")

    return redirect(url_for("budgets.index", month=target_month))
