from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.routes.auth import login_required
from app.forms.category_forms import CategoryForm
from app.services.category_service import CategoryService

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")
category_service = CategoryService()


@categories_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    income_categories = category_service.get_user_categories(user_id, type_="income")
    expense_categories = category_service.get_user_categories(user_id, type_="expense")
    return render_template(
        "categories/index.html",
        income_categories=income_categories,
        expense_categories=expense_categories,
    )


@categories_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    user_id = session["user_id"]
    form = CategoryForm()

    if form.validate_on_submit():
        category, error = category_service.create_category(
            name=form.name.data,
            type_=form.type.data,
            user_id=user_id,
            color=form.color.data,
        )
        if error:
            flash(error, "danger")
        else:
            flash(f"Category '{category.name}' created successfully!", "success")
            return redirect(url_for("categories.index"))

    return render_template("categories/form.html", form=form, title="New Category")


@categories_bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def edit(category_id: int):
    user_id = session["user_id"]
    category = category_service.get_category_by_id(category_id, user_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for("categories.index"))

    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        updated, error = category_service.update_category(
            category_id=category_id,
            user_id=user_id,
            name=form.name.data,
            type_=form.type.data,
            color=form.color.data,
        )
        if error:
            flash(error, "danger")
        else:
            flash(f"Category '{updated.name}' updated successfully!", "success")
            return redirect(url_for("categories.index"))

    return render_template(
        "categories/form.html",
        form=form,
        title="Edit Category",
        category=category,
    )


@categories_bp.route("/<int:category_id>/delete", methods=["POST"])
@login_required
def delete(category_id: int):
    user_id = session["user_id"]
    success, error = category_service.delete_category(category_id, user_id)
    if success:
        flash("Category deleted successfully.", "success")
    else:
        flash(error or "Failed to delete category.", "danger")
    return redirect(url_for("categories.index"))
