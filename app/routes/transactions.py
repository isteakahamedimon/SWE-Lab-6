from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
    Response,
)
from datetime import date
from app.routes.auth import login_required
from app.forms.transaction_forms import (
    TransactionForm,
    TransactionFilterForm,
    TransactionImportForm,
)
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")
transaction_service = TransactionService()
category_service = CategoryService()


def _populate_category_choices(form, user_id: int, type_filter: str = None):
    cats = category_service.get_user_categories(user_id, type_=type_filter)
    form.category_id.choices = [(c.id, f"{c.name} ({c.type})") for c in cats]


@transactions_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    filter_form = TransactionFilterForm(request.args)

    # Populate categories for filter dropdown
    user_cats = category_service.get_user_categories(user_id)
    filter_form.category_id.choices = [(0, "All Categories")] + [
        (c.id, f"{c.name} ({c.type})") for c in user_cats
    ]

    start_date = filter_form.start_date.data if filter_form.start_date.data else None
    end_date = filter_form.end_date.data if filter_form.end_date.data else None
    category_id = (
        filter_form.category_id.data
        if filter_form.category_id.data and filter_form.category_id.data > 0
        else None
    )
    t_type = (
        filter_form.type.data
        if filter_form.type.data and filter_form.type.data != "all"
        else None
    )
    keyword = filter_form.keyword.data if filter_form.keyword.data else None
    sort_by = filter_form.sort_by.data or "date"
    sort_order = filter_form.sort_order.data or "desc"

    transactions = transaction_service.get_transactions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        type_=t_type,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")
    net_filtered = total_income - total_expense

    return render_template(
        "transactions/index.html",
        transactions=transactions,
        filter_form=filter_form,
        total_income=total_income,
        total_expense=total_expense,
        net_filtered=net_filtered,
    )


@transactions_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    user_id = session["user_id"]
    form = TransactionForm()

    user_cats = category_service.get_user_categories(user_id)
    if not user_cats:
        flash("Please create at least one category before adding transactions.", "warning")
        return redirect(url_for("categories.new"))

    form.category_id.choices = [(c.id, f"{c.name} ({c.type})") for c in user_cats]

    if form.validate_on_submit():
        transaction, error = transaction_service.create_transaction(
            amount=float(form.amount.data),
            type_=form.type.data,
            category_id=form.category_id.data,
            user_id=user_id,
            date_val=form.date.data,
            description=form.description.data,
        )
        if error:
            flash(error, "danger")
        else:
            flash("Transaction added successfully!", "success")
            return redirect(url_for("transactions.index"))

    return render_template("transactions/form.html", form=form, title="New Transaction")


@transactions_bp.route("/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit(transaction_id: int):
    user_id = session["user_id"]
    transaction = transaction_service.get_transaction_by_id(transaction_id, user_id)
    if not transaction:
        flash("Transaction not found.", "danger")
        return redirect(url_for("transactions.index"))

    form = TransactionForm(obj=transaction)
    user_cats = category_service.get_user_categories(user_id)
    form.category_id.choices = [(c.id, f"{c.name} ({c.type})") for c in user_cats]

    if form.validate_on_submit():
        updated, error = transaction_service.update_transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=float(form.amount.data),
            type_=form.type.data,
            category_id=form.category_id.data,
            date_val=form.date.data,
            description=form.description.data,
        )
        if error:
            flash(error, "danger")
        else:
            flash("Transaction updated successfully!", "success")
            return redirect(url_for("transactions.index"))

    return render_template(
        "transactions/form.html",
        form=form,
        title="Edit Transaction",
        transaction=transaction,
    )


@transactions_bp.route("/<int:transaction_id>/delete", methods=["POST"])
@login_required
def delete(transaction_id: int):
    user_id = session["user_id"]
    success, error = transaction_service.delete_transaction(transaction_id, user_id)
    if success:
        flash("Transaction deleted successfully.", "success")
    else:
        flash(error or "Failed to delete transaction.", "danger")
    return redirect(url_for("transactions.index"))


@transactions_bp.route("/export")
@login_required
def export_csv():
    user_id = session["user_id"]
    t_type = request.args.get("type")
    csv_data = transaction_service.export_transactions_csv(
        user_id=user_id,
        type_=t_type if t_type in ("income", "expense") else None,
    )
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=expensetrack_export_{date.today()}.csv"},
    )


@transactions_bp.route("/import", methods=["GET", "POST"])
@login_required
def import_csv():
    user_id = session["user_id"]
    form = TransactionImportForm()

    if form.validate_on_submit():
        file_obj = form.file.data
        adapter_type = form.adapter_type.data
        try:
            content = file_obj.read().decode("utf-8")
            count, errors = transaction_service.import_transactions(
                user_id=user_id, content=content, adapter_type=adapter_type
            )
            if count > 0:
                flash(f"Successfully imported {count} transaction(s)!", "success")
            for err in errors[:5]:
                flash(err, "warning")
            if not errors and count > 0:
                return redirect(url_for("transactions.index"))
        except Exception as e:
            flash(f"Error reading file: {str(e)}", "danger")

    return render_template("transactions/import.html", form=form)
