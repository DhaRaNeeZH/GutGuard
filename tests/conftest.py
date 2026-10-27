"""
Pytest configuration and shared test fixtures for GutGuard.
Uses in-memory SQLite database for high-speed, isolated test execution.
"""
import sys
from pathlib import Path
import pytest

# Ensure project root is on sys.path during testing
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app import create_app
from backend.config import TestingConfig
from backend.extensions import db as _db
from database.models import Role, User, FoodCategory, FoodCatalogue


@pytest.fixture(scope="session")
def app():
    """Create application configured for testing."""
    app = create_app(TestingConfig)
    return app


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        _db.create_all()

        # Seed roles
        student_role = Role(name="student")
        admin_role = Role(name="admin")
        _db.session.add_all([student_role, admin_role])

        # Seed basic food category and items
        cat = FoodCategory(name="South Indian Breakfast", sort_order=1)
        _db.session.add(cat)
        _db.session.flush()

        food1 = FoodCatalogue(
            name="Idli",
            name_normalized="idli",
            category_id=cat.id,
            region="South Indian",
            is_vegetarian=True,
            status="active",
            is_verified=True,
        )
        food2 = FoodCatalogue(
            name="Dosa",
            name_normalized="dosa",
            category_id=cat.id,
            region="South Indian",
            is_vegetarian=True,
            status="active",
            is_verified=True,
        )
        _db.session.add_all([food1, food2])
        _db.session.commit()

        yield _db

        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def student_user(db):
    """Create and return a sample student user."""
    role = Role.query.filter_by(name="student").first()
    user = User(
        email="student@college.edu",
        display_name="Test Student",
        student_id="MCA202601",
        role=role,
    )
    user.set_password("StudentPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """Create and return a sample admin user."""
    role = Role.query.filter_by(name="admin").first()
    admin = User(
        email="admin@gutguard.local",
        display_name="Site Administrator",
        role=role,
    )
    admin.set_password("AdminPass123!")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def auth_client(client, student_user):
    """Client with active student session."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(student_user.id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client with active admin session."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user.id)
        sess["_fresh"] = True
    return client
