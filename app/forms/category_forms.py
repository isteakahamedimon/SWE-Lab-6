from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class CategoryForm(FlaskForm):
    name = StringField(
        "Category Name",
        validators=[
            DataRequired(message="Category name is required"),
            Length(min=1, max=64, message="Category name must be 1 to 64 characters"),
        ],
        render_kw={"placeholder": "e.g. Groceries, Streaming Services, Side Gig"},
    )
    type = SelectField(
        "Type",
        choices=[("expense", "Expense"), ("income", "Income")],
        validators=[DataRequired()],
    )
    color = StringField(
        "Badge Color",
        default="#4e73df",
        validators=[
            Regexp(r"^#[0-9a-fA-F]{6}$", message="Please choose a valid hex color, e.g. #4e73df"),
        ],
        render_kw={"type": "color"},
    )
    submit = SubmitField("Save Category")
