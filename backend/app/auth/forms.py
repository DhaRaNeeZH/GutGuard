"""WTForms definitions for authentication."""
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def valid_email(form, field):
    """Validates email format safely offline and across college/local domains."""
    val = (field.data or "").strip()
    if not val or not EMAIL_REGEX.match(val):
        raise ValidationError("Please enter a valid email address.")


class LoginForm(FlaskForm):
    email       = StringField("Email", validators=[DataRequired(), valid_email])
    password    = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me signed in")
    submit      = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    display_name = StringField("Your Name", validators=[DataRequired(), Length(2, 100)])
    email        = StringField("College Email", validators=[DataRequired(), valid_email])
    student_id   = StringField("Roll / Student ID (optional)", validators=[Optional(), Length(max=32)])
    password     = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Create Account")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password     = PasswordField("New Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(),
        EqualTo("new_password", message="Passwords must match.")
    ])
    submit = SubmitField("Update Password")
