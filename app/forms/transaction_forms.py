from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    DecimalField,
    SelectField,
    DateField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class TransactionForm(FlaskForm):
    amount = DecimalField(
        "Amount ($)",
        places=2,
        validators=[
            DataRequired(message="Amount is required"),
            NumberRange(min=0.01, message="Amount must be greater than 0"),
        ],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )
    type = SelectField(
        "Type",
        choices=[("expense", "Expense"), ("income", "Income")],
        validators=[DataRequired()],
    )
    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Please select a category")],
    )
    date = DateField(
        "Date",
        default=date.today,
        validators=[DataRequired(message="Valid date is required")],
    )
    description = StringField(
        "Description / Note",
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "e.g. Weekly supermarket shopping, Freelance invoice #102"},
    )
    submit = SubmitField("Save Transaction")


class TransactionFilterForm(FlaskForm):
    start_date = DateField("From Date", validators=[Optional()])
    end_date = DateField("To Date", validators=[Optional()])
    type = SelectField(
        "Type",
        choices=[("all", "All Types"), ("expense", "Expense"), ("income", "Income")],
        default="all",
        validators=[Optional()],
    )
    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[Optional()],
    )
    keyword = StringField(
        "Search Keyword",
        validators=[Optional()],
        render_kw={"placeholder": "Search description..."},
    )
    sort_by = SelectField(
        "Sort By",
        choices=[("date", "Date"), ("amount", "Amount")],
        default="date",
    )
    sort_order = SelectField(
        "Order",
        choices=[("desc", "Newest / Highest First"), ("asc", "Oldest / Lowest First")],
        default="desc",
    )
    submit = SubmitField("Filter")


class TransactionImportForm(FlaskForm):
    file = FileField(
        "CSV File",
        validators=[
            FileRequired(message="Please choose a CSV file"),
            FileAllowed(["csv"], "Only .csv files are supported!"),
        ],
    )
    adapter_type = SelectField(
        "CSV Format / Structure",
        choices=[
            ("simple", "Simple Format (Date, Type, Category, Amount, Description)"),
            ("bank", "Bank Statement Format (Date, Details, Debit, Credit)"),
        ],
        default="simple",
    )
    submit = SubmitField("Upload & Import")
