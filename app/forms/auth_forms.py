from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required"),
            Length(min=3, max=64, message="Username must be between 3 and 64 characters"),
        ],
        render_kw={"placeholder": "e.g. johndoe", "autocomplete": "username"},
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
            Length(max=120),
        ],
        render_kw={"placeholder": "e.g. john@example.com", "autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=6, message="Password must be at least 6 characters"),
        ],
        render_kw={"placeholder": "Minimum 6 characters", "autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
        render_kw={"placeholder": "Re-enter password", "autocomplete": "new-password"},
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    username_or_email = StringField(
        "Username or Email",
        validators=[DataRequired(message="Please enter your username or email")],
        render_kw={"placeholder": "Username or email", "autocomplete": "username"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password")],
        render_kw={"placeholder": "Password", "autocomplete": "current-password"},
    )
    submit = SubmitField("Log In")
