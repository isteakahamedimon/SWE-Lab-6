from datetime import date
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Regexp


class BudgetForm(FlaskForm):
    category_id = SelectField(
        "Expense Category",
        coerce=int,
        validators=[DataRequired(message="Please select an expense category")],
    )
    month = StringField(
        "Month (YYYY-MM)",
        default=lambda: date.today().strftime("%Y-%m"),
        validators=[
            DataRequired(message="Month is required"),
            Regexp(r"^\d{4}-(0[1-9]|1[0-2])$", message="Month must be in YYYY-MM format, e.g. 2026-10"),
        ],
        render_kw={"placeholder": "YYYY-MM", "type": "month"},
    )
    amount = DecimalField(
        "Monthly Budget Limit ($)",
        places=2,
        validators=[
            DataRequired(message="Budget limit amount is required"),
            NumberRange(min=1.0, message="Budget amount must be at least $1.00"),
        ],
        render_kw={"placeholder": "e.g. 500.00", "step": "0.01"},
    )
    submit = SubmitField("Save Budget")
