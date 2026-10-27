"""Meal logging routes – CRUD for meals and meal items, water logging."""
from datetime import datetime, timezone, date
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, abort
)
from flask_login import login_required, current_user
from sqlalchemy import func, desc

from . import meals_bp
try:
    from backend.extensions import db, csrf
    from database.models import Meal, MealItem, FoodCatalogue, CustomFood, WaterLog
except ImportError:
    from extensions import db, csrf
    from models import Meal, MealItem, FoodCatalogue, CustomFood, WaterLog


# ─── Journal (calendar view) ──────────────────────────────────────────────────

@meals_bp.route("/journal")
@login_required
def journal():
    """Date-based meal journal."""
    date_str = request.args.get("date")
    try:
        view_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        view_date = date.today()

    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"

    meals_q = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.meal_date) == view_date,
    )
    if not is_demo_user:
        meals_q = meals_q.filter(Meal.is_demo == False)
    meals = meals_q.order_by(Meal.meal_date).all()

    water_q = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        func.date(WaterLog.logged_at) == view_date,
    )
    if not is_demo_user:
        water_q = water_q.filter(WaterLog.is_demo == False)
    water_logs = water_q.order_by(WaterLog.logged_at).all()

    return render_template(
        "meals/journal.html",
        view_date=view_date,
        today=date.today(),
        meals=meals,
        water_logs=water_logs,
    )


# ─── Log a Meal ───────────────────────────────────────────────────────────────

@meals_bp.route("/log", methods=["GET", "POST"])
@login_required
def log_meal():
    """Create a new meal with multiple food items."""
    if request.method == "POST":
        meal_type = request.form.get("meal_type")
        meal_date_str = request.form.get("meal_date")
        notes = request.form.get("notes", "").strip()

        # Validate meal type
        valid_types = ("breakfast", "lunch", "dinner", "snack")
        if meal_type not in valid_types:
            flash("Please select a valid meal type.", "danger")
            return redirect(url_for("meals.log_meal"))

        # Parse datetime – default to now if missing
        try:
            meal_dt = datetime.fromisoformat(meal_date_str).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            meal_dt = datetime.now(timezone.utc)

        meal = Meal(
            user_id=current_user.id,
            meal_type=meal_type,
            meal_date=meal_dt,
            notes=notes or None,
        )
        db.session.add(meal)
        db.session.flush()  # Get meal.id before adding items

        # Process food items submitted via the multi-item form
        item_count = 0
        food_ids    = request.form.getlist("food_id[]")
        custom_names= request.form.getlist("custom_food_name[]")
        quantities  = request.form.getlist("quantity[]")
        units       = request.form.getlist("unit[]")
        item_notes  = request.form.getlist("item_notes[]")

        for i, food_id in enumerate(food_ids):
            qty   = quantities[i] if i < len(quantities) else None
            unit  = units[i]      if i < len(units)      else None
            inote = item_notes[i] if i < len(item_notes) else None

            try:
                qty_f = float(qty) if qty else None
            except ValueError:
                qty_f = None

            if food_id and food_id != "custom":
                # Catalogue food
                food = db.session.get(FoodCatalogue, int(food_id))
                if food:
                    item = MealItem(
                        meal_id=meal.id,
                        food_id=food.id,
                        quantity=qty_f,
                        unit=unit or None,
                        notes=inote or None,
                    )
                    db.session.add(item)
                    item_count += 1
            else:
                # Custom food by name
                name = (custom_names[i] if i < len(custom_names) else "").strip()
                if name:
                    name_norm = name.lower().strip()
                    # Reuse existing custom food from this user if available
                    custom = CustomFood.query.filter_by(
                        submitted_by_id=current_user.id,
                        name_normalized=name_norm
                    ).first()
                    if not custom:
                        custom = CustomFood(
                            submitted_by_id=current_user.id,
                            name=name,
                            name_normalized=name_norm,
                        )
                        db.session.add(custom)
                        db.session.flush()
                    item = MealItem(
                        meal_id=meal.id,
                        custom_food_id=custom.id,
                        quantity=qty_f,
                        unit=unit or None,
                        notes=inote or None,
                    )
                    db.session.add(item)
                    item_count += 1

        if item_count == 0:
            db.session.rollback()
            flash("Please add at least one food item to the meal.", "warning")
            return redirect(url_for("meals.log_meal"))

        db.session.commit()
        flash(f"Meal logged successfully with {item_count} item(s)!", "success")
        return redirect(url_for("meals.journal", date=meal_dt.date().isoformat()))

    # GET – show the logging form
    return render_template("meals/log_meal.html",
                           now=datetime.now(timezone.utc))


# ─── Edit / Delete Meal ────────────────────────────────────────────────────────

@meals_bp.route("/<int:meal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_meal(meal_id):
    """Edit an existing meal (type, time, notes) and its items."""
    meal = db.get_or_404(Meal, meal_id)
    if meal.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        meal_type = request.form.get("meal_type")
        meal_date_str = request.form.get("meal_date")
        notes = request.form.get("notes", "").strip()

        valid_types = ("breakfast", "lunch", "dinner", "snack")
        if meal_type not in valid_types:
            flash("Invalid meal type.", "danger")
        else:
            try:
                meal_dt = datetime.fromisoformat(meal_date_str).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                meal_dt = meal.meal_date

            meal.meal_type = meal_type
            meal.meal_date = meal_dt
            meal.notes = notes or None
            db.session.commit()
            flash("Meal updated.", "success")
            return redirect(url_for("meals.journal", date=meal_dt.date().isoformat()))

    return render_template("meals/edit_meal.html", meal=meal)


@meals_bp.route("/<int:meal_id>/delete", methods=["POST"])
@login_required
def delete_meal(meal_id):
    """Delete a meal and all its items."""
    meal = db.get_or_404(Meal, meal_id)
    if meal.user_id != current_user.id:
        abort(403)
    meal_date = meal.meal_date.date().isoformat()
    db.session.delete(meal)
    db.session.commit()
    flash("Meal deleted.", "info")
    return redirect(url_for("meals.journal", date=meal_date))


# ─── Water Logging ────────────────────────────────────────────────────────────

@meals_bp.route("/water/log", methods=["POST"])
@login_required
def log_water():
    """Log a water intake entry."""
    quantity_str = request.form.get("quantity", "").strip()
    unit = request.form.get("unit", "ml")
    date_str = request.form.get("date")
    notes = request.form.get("notes", "").strip()

    try:
        qty = float(quantity_str) if quantity_str else None
    except ValueError:
        qty = None

    try:
        log_dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        log_dt = datetime.now(timezone.utc)

    wlog = WaterLog(
        user_id=current_user.id,
        quantity=qty,
        unit=unit,
        logged_at=log_dt,
        notes=notes or None,
    )
    db.session.add(wlog)
    db.session.commit()
    flash("Water intake logged.", "success")
    return redirect(url_for("meals.journal", date=log_dt.date().isoformat()))


@meals_bp.route("/water/<int:log_id>/delete", methods=["POST"])
@login_required
def delete_water(log_id):
    """Delete a water log entry."""
    wlog = db.get_or_404(WaterLog, log_id)
    if wlog.user_id != current_user.id:
        abort(403)
    log_date = wlog.logged_at.date().isoformat()
    db.session.delete(wlog)
    db.session.commit()
    flash("Water entry removed.", "info")
    return redirect(url_for("meals.journal", date=log_date))
