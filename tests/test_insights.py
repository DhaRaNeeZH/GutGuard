"""
Tests for habit insights page, rule-based alerts engine, and Chart.js data API.
"""
from datetime import datetime, timezone, timedelta, date
from database.models import Meal, MealItem, FoodCatalogue


def test_insights_page_empty(auth_client):
    """Insights page displays properly with zero logged meals."""
    res = auth_client.get("/insights/")
    assert res.status_code == 200
    assert b"Weekly Insights" in res.data
    assert b"About These Figures" in res.data


def test_insights_with_meals_and_rule_alerts(auth_client, student_user, db):
    """Rule engine generates transparent observations when meal patterns emerge."""
    today = date.today()
    food = FoodCatalogue.query.first()

    # Log snack meals (more snacks than main meals to trigger GG-003)
    for i in range(5):
        m = Meal(
            user_id=student_user.id,
            meal_type="snack",
            meal_date=datetime(today.year, today.month, today.day, 16, 0, tzinfo=timezone.utc),
            is_demo=False,
        )
        db.session.add(m)
        db.session.flush()
        db.session.add(MealItem(meal_id=m.id, food_id=food.id, quantity=1, unit="piece"))

    # Add 1 lunch
    m_lunch = Meal(
        user_id=student_user.id,
        meal_type="lunch",
        meal_date=datetime(today.year, today.month, today.day, 13, 0, tzinfo=timezone.utc),
        is_demo=False,
    )
    db.session.add(m_lunch)
    db.session.flush()
    db.session.add(MealItem(meal_id=m_lunch.id, food_id=food.id, quantity=1, unit="plate"))
    db.session.commit()

    res = auth_client.get("/insights/")
    assert res.status_code == 200
    # Rule GG-003 observation for snack-heavy
    assert b"GG-003" in res.data
    assert b"More Snacks Than Main Meals Logged" in res.data


def test_insights_demo_data_excluded(auth_client, student_user, db):
    """Synthetic demo records (is_demo=True) are strictly excluded from calculations."""
    today = date.today()
    demo_meal = Meal(
        user_id=student_user.id,
        meal_type="breakfast",
        meal_date=datetime(today.year, today.month, today.day, 8, 0, tzinfo=timezone.utc),
        is_demo=True,
    )
    db.session.add(demo_meal)
    db.session.commit()

    res = auth_client.get("/insights/api/weekly-data")
    assert res.status_code == 200
    data = res.get_json()
    assert data["type_counts"]["breakfast"] == 0


def test_insights_weekly_api(auth_client, student_user, db):
    """Weekly chart API returns expected structure with 7 day labels and meal counts."""
    res = auth_client.get("/insights/api/weekly-data")
    assert res.status_code == 200
    data = res.get_json()
    assert "labels" in data
    assert "meals_count" in data
    assert "type_counts" in data
    assert len(data["labels"]) == 7
