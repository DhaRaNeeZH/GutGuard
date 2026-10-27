"""Insights routes – rule-based habit analysis and weekly trends."""
from datetime import datetime, timezone, timedelta, date
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from . import insights_bp
try:
    from backend.extensions import db
    from database.models import Meal, MealItem, WaterLog, FoodCatalogue, FoodCategory
except ImportError:
    from extensions import db
    from models import Meal, MealItem, WaterLog, FoodCatalogue, FoodCategory


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_week_range(offset: int = 0):
    """Return (week_start, week_end) dates for the week offset from current."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=offset)
    week_end   = week_start + timedelta(days=6)
    return week_start, week_end


def _meals_in_range(user_id: int, start: date, end: date, include_demo: bool = False):
    q = Meal.query.filter(
        Meal.user_id == user_id,
        func.date(Meal.meal_date) >= start,
        func.date(Meal.meal_date) <= end,
    )
    if not include_demo:
        q = q.filter(Meal.is_demo == False)
    return q.all()


# ─── Routes ───────────────────────────────────────────────────────────────────

@insights_bp.route("/")
@login_required
def index():
    """Weekly insights page."""
    offset = request.args.get("week_offset", 0, type=int)
    week_start, week_end = _get_week_range(offset)
    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"

    meals = _meals_in_range(current_user.id, week_start, week_end, include_demo=is_demo_user)

    # ── Meal type distribution ─────────────────────────────
    type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    for m in meals:
        type_counts[m.meal_type] = type_counts.get(m.meal_type, 0) + 1

    # ── Days with logged meals ─────────────────────────────
    days_with_meals = sorted({m.meal_date.date() for m in meals})
    total_days = (week_end - week_start).days + 1
    days_elapsed = min((date.today() - week_start).days + 1, total_days)
    consistency_pct = round(len(days_with_meals) / max(days_elapsed, 1) * 100)

    # ── Meals per day for the bar chart ───────────────────
    meals_per_day = {}
    current_day = week_start
    while current_day <= week_end:
        meals_per_day[current_day.isoformat()] = 0
        current_day += timedelta(days=1)
    for m in meals:
        key = m.meal_date.date().isoformat()
        if key in meals_per_day:
            meals_per_day[key] += 1

    # ── Category distribution ─────────────────────────────
    cat_counts: dict[str, int] = {}
    for meal in meals:
        for item in meal.items:
            if item.food and item.food.category:
                cat = item.food.category.name
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # ── Rule-based habit alerts ────────────────────────────
    alerts = _compute_alerts(meals, week_start, week_end)

    # ── Water this week ───────────────────────────────────
    water_q = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        func.date(WaterLog.logged_at) >= week_start,
        func.date(WaterLog.logged_at) <= week_end,
    )
    if not is_demo_user:
        water_q = water_q.filter(WaterLog.is_demo == False)
    water_logs = water_q.all()
    total_water_ml = sum((w.quantity or 0) for w in water_logs if w.unit == "ml")

    return render_template(
        "insights/index.html",
        week_start=week_start,
        week_end=week_end,
        week_offset=offset,
        meals=meals,
        type_counts=type_counts,
        days_with_meals=days_with_meals,
        total_days=total_days,
        days_elapsed=days_elapsed,
        consistency_pct=consistency_pct,
        meals_per_day=meals_per_day,
        cat_counts=cat_counts,
        alerts=alerts,
        total_water_ml=total_water_ml,
        today=date.today(),
    )


@insights_bp.route("/api/weekly-data")
@login_required
def weekly_data_api():
    """JSON endpoint for Chart.js – returns data for the current week."""
    offset = request.args.get("week_offset", 0, type=int)
    week_start, week_end = _get_week_range(offset)
    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"
    meals = _meals_in_range(current_user.id, week_start, week_end, include_demo=is_demo_user)

    labels = []
    counts = []
    current_day = week_start
    while current_day <= week_end:
        labels.append(current_day.strftime("%a %d"))
        day_meals = [m for m in meals if m.meal_date.date() == current_day]
        counts.append(len(day_meals))
        current_day += timedelta(days=1)

    type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    for m in meals:
        type_counts[m.meal_type] += 1

    return jsonify({
        "labels":      labels,
        "meals_count": counts,
        "type_counts": type_counts,
    })


# ─── Rule Engine ──────────────────────────────────────────────────────────────

def _compute_alerts(meals: list, week_start: date, week_end: date) -> list[dict]:
    """
    Transparent, rule-based habit awareness alerts.

    Rules are documented, configurable, and labeled clearly.
    These are OBSERVATIONS about recorded data, not medical assessments.

    Returns a list of alert dicts:
      {type: 'info'|'warning', title, message, rule_id, supporting_data}
    """
    alerts = []
    total_days = (week_end - week_start).days + 1
    days_elapsed = min((date.today() - week_start).days + 1, total_days)

    # Collect days with meals
    days_with_meals = {m.meal_date.date() for m in meals}
    days_without = days_elapsed - len(days_with_meals)

    # ── Rule GG-001: Meal logging consistency ─────────────
    # Threshold: fewer than 50% of elapsed days have any logged meal.
    # This is a configurable project rule, not a medical threshold.
    if days_elapsed >= 3 and len(days_with_meals) / days_elapsed < 0.5:
        alerts.append({
            "type":    "info",
            "rule_id": "GG-001",
            "title":   "Low Logging Activity This Week",
            "message": (
                f"You've logged meals on {len(days_with_meals)} of {days_elapsed} days so far this week. "
                "Regular logging helps you spot your own patterns more easily."
            ),
            "note": "Rule GG-001: Fewer than 50% of elapsed days have a logged meal (project threshold).",
        })

    # ── Rule GG-002: Missing breakfast ────────────────────
    # Only applicable when at least 3 days have passed.
    if days_elapsed >= 3:
        breakfasts = [m for m in meals if m.meal_type == "breakfast"]
        days_with_breakfast = {m.meal_date.date() for m in breakfasts}
        # Caution: we only know about LOGGED breakfasts, not whether
        # the student actually skipped. We word this carefully.
        if len(days_with_breakfast) == 0:
            alerts.append({
                "type":    "info",
                "rule_id": "GG-002",
                "title":   "No Breakfasts Logged This Week",
                "message": (
                    "No breakfast entries appear in your log for this week. "
                    "If you have been eating breakfast and not logging it, "
                    "adding those entries will give you a more complete picture."
                ),
                "note": "Rule GG-002: Zero breakfast entries in the current week (observation only).",
            })

    # ── Rule GG-003: Snack-heavy pattern ──────────────────
    snacks = [m for m in meals if m.meal_type == "snack"]
    main_meals = [m for m in meals if m.meal_type in ("breakfast", "lunch", "dinner")]
    if len(meals) >= 5 and len(snacks) > len(main_meals):
        alerts.append({
            "type":    "info",
            "rule_id": "GG-003",
            "title":   "More Snacks Than Main Meals Logged",
            "message": (
                f"You've logged {len(snacks)} snacks and {len(main_meals)} main meals this week. "
                "This observation is based only on what you've logged — it's worth reviewing "
                "whether your main meals are being recorded."
            ),
            "note": "Rule GG-003: Snack entries exceed main meal entries (observation only).",
        })

    # ── Rule GG-004: Good consistency ─────────────────────
    if days_elapsed >= 3 and len(days_with_meals) / days_elapsed >= 0.85:
        alerts.append({
            "type":    "success",
            "rule_id": "GG-004",
            "title":   "Great Logging Consistency!",
            "message": (
                f"You've logged meals on {len(days_with_meals)} of {days_elapsed} days. "
                "Consistent logging makes your weekly summary more reliable."
            ),
            "note": "Rule GG-004: ≥85% of elapsed days have a logged meal.",
        })

    return alerts
