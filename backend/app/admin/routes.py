"""Admin routes – protected catalogue management."""
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import desc

from . import admin_bp
try:
    from backend.extensions import db
    from database.models import (
        FoodCatalogue, FoodCategory, FoodAlias,
        CustomFood, User
    )
except ImportError:
    from extensions import db
    from models import (
        FoodCatalogue, FoodCategory, FoodAlias,
        CustomFood, User
    )


def admin_required(f):
    """Decorator: require admin role. Server-side, not just UI hiding."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def index():
    """Admin dashboard."""
    total_foods    = FoodCatalogue.query.filter_by(status="active").count()
    pending_custom = CustomFood.query.filter_by(review_status="pending").count()
    total_students = User.query.join(User.role).filter_by(name="student").count()
    return render_template(
        "admin/index.html",
        total_foods=total_foods,
        pending_custom=pending_custom,
        total_students=total_students,
    )


@admin_bp.route("/catalogue")
@login_required
@admin_required
def catalogue():
    """Browse and manage the food catalogue."""
    q = request.args.get("q", "").strip().lower()
    foods_q = FoodCatalogue.query
    if q:
        foods_q = foods_q.filter(FoodCatalogue.name_normalized.contains(q))
    foods = foods_q.order_by(FoodCatalogue.name).limit(100).all()
    return render_template("admin/catalogue.html", foods=foods, q=q)


@admin_bp.route("/catalogue/<int:food_id>/verify", methods=["POST"])
@login_required
@admin_required
def verify_food(food_id):
    """Mark a food as verified."""
    food = db.get_or_404(FoodCatalogue, food_id)
    food.is_verified = True
    db.session.commit()
    flash(f"'{food.name}' marked as verified.", "success")
    return redirect(url_for("admin.catalogue"))


@admin_bp.route("/custom-foods")
@login_required
@admin_required
def custom_foods():
    """Review pending custom food submissions."""
    foods = (
        CustomFood.query
        .filter_by(review_status="pending")
        .order_by(desc(CustomFood.submitted_at))
        .all()
    )
    return render_template("admin/custom_foods.html", foods=foods)


@admin_bp.route("/custom-foods/<int:food_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_custom(food_id):
    """Promote a custom food to the main catalogue."""
    from datetime import datetime, timezone
    custom = db.get_or_404(CustomFood, food_id)
    # Create catalogue entry
    cat_food = FoodCatalogue(
        name=custom.name,
        name_normalized=custom.name_normalized,
        status="active",
        is_verified=True,
        data_source="Promoted from user submission",
    )
    db.session.add(cat_food)
    db.session.flush()

    custom.review_status = "approved"
    custom.catalogue_food_id = cat_food.id
    custom.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"'{custom.name}' added to catalogue.", "success")
    return redirect(url_for("admin.custom_foods"))


@admin_bp.route("/custom-foods/<int:food_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_custom(food_id):
    """Reject a custom food submission."""
    from datetime import datetime, timezone
    custom = db.get_or_404(CustomFood, food_id)
    custom.review_status = "rejected"
    custom.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"Submission '{custom.name}' rejected.", "info")
    return redirect(url_for("admin.custom_foods"))
