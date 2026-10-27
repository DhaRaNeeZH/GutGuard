"""
Tests for meal journal, logging, editing, deleting meals, and water tracking.
"""
from datetime import datetime, timezone, date
from database.models import Meal, MealItem, CustomFood, WaterLog, FoodCatalogue, Role, User


def test_journal_view_empty(auth_client):
    """Journal page loads with empty day view."""
    res = auth_client.get("/meals/journal")
    assert res.status_code == 200
    assert b"Meal Journal" in res.data
    assert b"No meals logged" in res.data


def test_log_meal_with_catalogue_food(auth_client, student_user, db):
    """Student logs a breakfast with catalogue item."""
    food = FoodCatalogue.query.filter_by(name="Idli").first()
    res = auth_client.post("/meals/log", data={
        "meal_type": "breakfast",
        "meal_date": "2026-10-19T08:30",
        "notes": "Mess breakfast before class",
        "food_id[]": [str(food.id)],
        "quantity[]": ["3"],
        "unit[]": ["piece"],
        "item_notes[]": ["with sambar"],
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Meal logged successfully" in res.data

    meal = Meal.query.filter_by(user_id=student_user.id).first()
    assert meal is not None
    assert meal.meal_type == "breakfast"
    assert len(meal.items) == 1
    assert meal.items[0].food.name == "Idli"
    assert meal.items[0].quantity == 3.0
    assert meal.items[0].unit == "piece"


def test_log_meal_with_custom_food(auth_client, student_user, db):
    """Student logs a meal with custom unlisted food."""
    res = auth_client.post("/meals/log", data={
        "meal_type": "snack",
        "meal_date": "2026-10-19T17:00",
        "notes": "Hostel room snack",
        "food_id[]": ["custom"],
        "custom_food_name[]": ["Makhana Roasted"],
        "quantity[]": ["1"],
        "unit[]": ["bowl"],
        "item_notes[]": ["homemade"],
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Meal logged successfully" in res.data

    custom = CustomFood.query.filter_by(name_normalized="makhana roasted").first()
    assert custom is not None
    assert custom.review_status == "pending"
    assert custom.submitted_by_id == student_user.id


def test_log_meal_without_items_fails(auth_client):
    """Submitting empty meal without food items shows a friendly warning."""
    res = auth_client.post("/meals/log", data={
        "meal_type": "lunch",
        "meal_date": "2026-10-19T13:00",
        "notes": "",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Please add at least one food item" in res.data


def test_edit_meal(auth_client, student_user, db):
    """Student can update meal type, notes, and timestamp."""
    food = FoodCatalogue.query.first()
    meal = Meal(
        user_id=student_user.id,
        meal_type="lunch",
        meal_date=datetime(2026, 10, 19, 13, 0, tzinfo=timezone.utc),
        notes="Initial note",
    )
    db.session.add(meal)
    db.session.flush()
    db.session.add(MealItem(meal_id=meal.id, food_id=food.id, quantity=1, unit="cup"))
    db.session.commit()

    res = auth_client.post(f"/meals/{meal.id}/edit", data={
        "meal_type": "dinner",
        "meal_date": "2026-10-19T20:30",
        "notes": "Updated dinner note",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Meal updated" in res.data
    db.session.refresh(meal)
    assert meal.meal_type == "dinner"
    assert meal.notes == "Updated dinner note"


def test_delete_meal_cascades(auth_client, student_user, db):
    """Deleting a meal also deletes associated meal items."""
    food = FoodCatalogue.query.first()
    meal = Meal(
        user_id=student_user.id,
        meal_type="snack",
        meal_date=datetime(2026, 10, 19, 16, 0, tzinfo=timezone.utc),
    )
    db.session.add(meal)
    db.session.flush()
    item = MealItem(meal_id=meal.id, food_id=food.id, quantity=1, unit="plate")
    db.session.add(item)
    db.session.commit()
    meal_id = meal.id
    item_id = item.id

    res = auth_client.post(f"/meals/{meal_id}/delete", follow_redirects=True)
    assert res.status_code == 200
    assert b"Meal deleted" in res.data
    assert db.session.get(Meal, meal_id) is None
    assert db.session.get(MealItem, item_id) is None


def test_cannot_delete_other_user_meal(client, student_user, db):
    """A user cannot delete another student's meal (403 forbidden)."""
    # Create second student
    role = Role.query.filter_by(name="student").first()
    other_user = User(email="other@college.edu", display_name="Other", role=role)
    other_user.set_password("pass123")
    db.session.add(other_user)
    db.session.flush()

    other_meal = Meal(
        user_id=other_user.id,
        meal_type="lunch",
        meal_date=datetime.now(timezone.utc),
    )
    db.session.add(other_meal)
    db.session.commit()

    # Log in as student_user
    with client.session_transaction() as sess:
        sess["_user_id"] = str(student_user.id)

    res = client.post(f"/meals/{other_meal.id}/delete")
    assert res.status_code == 403


def test_log_water_and_delete(auth_client, student_user, db):
    """Student logs water intake and can delete entry."""
    res = auth_client.post("/meals/water/log", data={
        "quantity": "500",
        "unit": "ml",
        "date": "2026-10-19T10:00",
        "notes": "Post gym bottle",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Water intake logged" in res.data
    wlog = WaterLog.query.filter_by(user_id=student_user.id).first()
    assert wlog is not None
    assert wlog.quantity == 500.0

    # Delete water log
    del_res = auth_client.post(f"/meals/water/{wlog.id}/delete", follow_redirects=True)
    assert del_res.status_code == 200
    assert b"Water entry removed" in del_res.data
    assert db.session.get(WaterLog, wlog.id) is None
