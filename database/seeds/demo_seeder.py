"""Demo data seeder – creates clearly-labelled synthetic records for development."""
from datetime import datetime, timezone, timedelta, date

try:
    from backend.extensions import db
    from database.models import User, Meal, MealItem, FoodCatalogue, WaterLog, Role
except ImportError:
    from extensions import db
    from models import User, Meal, MealItem, FoodCatalogue, WaterLog, Role


def seed_demo_meals():
    """
    Create demo meal records for the first student user.
    All records have is_demo=True so they are NEVER included in real analysis.
    """
    # Find any existing student user to attach demo data to
    student_role = Role.query.filter_by(name="student").first()
    if not student_role:
        print("[demo] No student role found. Run flask init-db first.")
        return

    demo_user = User.query.filter(
        User.role_id == student_role.id
    ).first()

    if not demo_user:
        # Create a demo user
        demo_user = User(
            email="demo@gutguard.local",
            display_name="Demo Student",
            student_id="DEMO001",
            role=student_role,
        )
        demo_user.set_password("demopassword123")
        db.session.add(demo_user)
        db.session.flush()
    else:
        demo_user.set_password("demopassword123")

    # Clear existing demo meals for this user (using session delete for proper cascade)
    existing_meals = Meal.query.filter_by(user_id=demo_user.id, is_demo=True).all()
    for m in existing_meals:
        db.session.delete(m)
    existing_water = WaterLog.query.filter_by(user_id=demo_user.id, is_demo=True).all()
    for w in existing_water:
        db.session.delete(w)
    db.session.flush()

    # Get a few foods
    food_names = ["Idli", "Dosa", "Sambar", "Plain Rice", "Chapati",
                  "Dal Makhani", "Tea", "Upma", "Curd Rice", "Boiled Egg"]
    foods = {
        f.name: f for f in
        FoodCatalogue.query.filter(FoodCatalogue.name.in_(food_names)).all()
    }

    today = date.today()

    def dt(days_ago: int, hour: int, minute: int = 0) -> datetime:
        d = today - timedelta(days=days_ago)
        return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)

    demo_meals = [
        # (days_ago, meal_type, hour, [(food_name, qty, unit)])
        (0,  "breakfast", 8,   [("Idli", 4, "piece"), ("Sambar", 1, "cup")]),
        (0,  "lunch",     13,  [("Plain Rice", 2, "cup"), ("Dal Makhani", 1, "cup")]),
        (0,  "snack",     16,  [("Tea", 1, "cup")]),
        (1,  "breakfast", 9,   [("Dosa", 2, "piece"), ("Sambar", 1, "cup")]),
        (1,  "lunch",     13,  [("Chapati", 3, "piece"), ("Dal Makhani", 1, "cup")]),
        (1,  "dinner",    20,  [("Curd Rice", 2, "cup")]),
        (2,  "breakfast", 8,   [("Upma", 1, "plate")]),
        (2,  "lunch",     14,  [("Plain Rice", 2, "cup"), ("Sambar", 1, "cup")]),
        (3,  "breakfast", 9,   [("Boiled Egg", 2, "piece"), ("Tea", 1, "cup")]),
        (3,  "snack",     16,  [("Tea", 1, "cup")]),
        (3,  "dinner",    21,  [("Chapati", 2, "piece")]),
        (4,  "breakfast", 8,   [("Idli", 3, "piece")]),
        (4,  "lunch",     13,  [("Plain Rice", 2, "cup")]),
        (5,  "breakfast", 8,   [("Dosa", 2, "piece")]),
        (5,  "lunch",     13,  [("Chapati", 3, "piece")]),
        (5,  "dinner",    20,  [("Plain Rice", 2, "cup"), ("Dal Makhani", 1, "cup")]),
        (6,  "breakfast", 9,   [("Upma", 1, "plate"), ("Tea", 1, "cup")]),
        (6,  "lunch",     13,  [("Plain Rice", 2, "cup"), ("Sambar", 1, "cup")]),
    ]

    for days_ago, meal_type, hour, items in demo_meals:
        meal = Meal(
            user_id=demo_user.id,
            meal_type=meal_type,
            meal_date=dt(days_ago, hour),
            notes="[DEMO DATA – not real student records]",
            is_demo=True,
        )
        db.session.add(meal)
        db.session.flush()

        for food_name, qty, unit in items:
            food = foods.get(food_name)
            if food:
                db.session.add(MealItem(
                    meal_id=meal.id,
                    food_id=food.id,
                    quantity=qty,
                    unit=unit,
                ))

    # Demo water logs
    for days_ago in range(7):
        for qty, hr in [(250, 8), (300, 12), (250, 15), (200, 19)]:
            db.session.add(WaterLog(
                user_id=demo_user.id,
                quantity=qty,
                unit="ml",
                logged_at=dt(days_ago, hr),
                notes="[DEMO DATA]",
                is_demo=True,
            ))

    db.session.commit()
    print(f"[demo] Demo meals seeded for user: {demo_user.email}")
