"""Authentication routes – register, login, logout, profile."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit

from . import auth_bp
from .forms import LoginForm, RegisterForm, ChangePasswordForm
try:
    from backend.extensions import db
    from database.models import User, Role
except ImportError:
    from extensions import db
    from models import User, Role


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            # Safe redirect – prevent open-redirect attacks
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc != "":
                next_page = url_for("main.dashboard")
            return redirect(next_page)
        flash("Invalid email or password. Please try again.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        # Check for duplicate email
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        student_role = Role.query.filter_by(name="student").first()
        user = User(
            email=form.email.data.lower().strip(),
            display_name=form.display_name.data.strip(),
            student_id=form.student_id.data.strip() or None,
            role=student_role,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Welcome to GutGuard. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
    return render_template("auth/profile.html", form=form)


@auth_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    """Self-service student account & data deletion (privacy / right to be forgotten)."""
    user = db.session.get(User, current_user.id)
    if user:
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash("Your account and all associated personal records have been permanently deleted.", "info")
    return redirect(url_for("main.landing"))
