"""Main routes – landing page and student dashboard."""
from datetime import datetime, timezone, timedelta
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc

from . import main_bp
try:
    from backend.extensions import db
    from database.models import Meal, MealItem, WaterLog
except ImportError:
    from extensions import db
    from models import Meal, MealItem, WaterLog


@main_bp.route("/")
def landing():
    """Public landing / welcome page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Student dashboard – today's meals, weekly overview, recent activity."""
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())

    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"

    # Today's meals
    meals_q = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.meal_date) == today,
    )
    if not is_demo_user:
        meals_q = meals_q.filter(Meal.is_demo == False)
    todays_meals = meals_q.order_by(Meal.meal_date).all()

    # Meals this week
    week_q = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.meal_date) >= week_start,
    )
    if not is_demo_user:
        week_q = week_q.filter(Meal.is_demo == False)
    week_meals = week_q.all()

    # Water today
    water_q = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        func.date(WaterLog.logged_at) == today,
    )
    if not is_demo_user:
        water_q = water_q.filter(WaterLog.is_demo == False)
    water_today = water_q.all()
    water_ml = sum(
        (w.quantity or 0) for w in water_today if w.unit == "ml"
    )

    # Weekly meal type counts for chart data
    meal_type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    for meal in week_meals:
        meal_type_counts[meal.meal_type] = meal_type_counts.get(meal.meal_type, 0) + 1

    # Days with at least one meal this week
    days_logged = len({m.meal_date.date() for m in week_meals})
    days_in_week = (today - week_start).days + 1  # Days elapsed so far this week

    # Recent 5 meals
    recent_q = Meal.query.filter(Meal.user_id == current_user.id)
    if not is_demo_user:
        recent_q = recent_q.filter(Meal.is_demo == False)
    recent_meals = recent_q.order_by(desc(Meal.meal_date)).limit(5).all()

    # Simple consistency percentage (based on days elapsed this week)
    consistency_pct = round((days_logged / max(days_in_week, 1)) * 100)

    return render_template(
        "main/dashboard.html",
        today=today,
        now=datetime.now(timezone.utc),
        todays_meals=todays_meals,
        week_meals=week_meals,
        water_ml=water_ml,
        meal_type_counts=meal_type_counts,
        days_logged=days_logged,
        days_in_week=days_in_week,
        consistency_pct=consistency_pct,
        recent_meals=recent_meals,
    )
