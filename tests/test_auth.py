"""
Tests for authentication: registration, login, logout, profile, and route protection.
"""
from database.models import User


def test_landing_page_accessible(client):
    """Public landing page loads for unauthenticated visitors."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"GutGuard" in res.data


def test_register_success(client, db):
    """User can register with valid details."""
    res = client.post("/auth/register", data={
        "display_name": "Rohan Sharma",
        "email": "rohan@college.edu",
        "student_id": "MCA202642",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Account created!" in res.data
    user = User.query.filter_by(email="rohan@college.edu").first()
    assert user is not None
    assert user.display_name == "Rohan Sharma"
    assert user.role.name == "student"


def test_register_duplicate_email(client, student_user):
    """Duplicate email registration is rejected."""
    res = client.post("/auth/register", data={
        "display_name": "Another Student",
        "email": student_user.email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"already exists" in res.data


def test_login_success(client, student_user):
    """User can log in with correct credentials."""
    res = client.post("/auth/login", data={
        "email": student_user.email,
        "password": "StudentPass123!",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Dashboard" in res.data


def test_login_invalid_password(client, student_user):
    """Incorrect password rejects login with error message."""
    res = client.post("/auth/login", data={
        "email": student_user.email,
        "password": "WrongPassword999",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Invalid email or password" in res.data


def test_logout(auth_client):
    """Logged in user can log out."""
    res = auth_client.get("/auth/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"logged out" in res.data


def test_protected_dashboard_redirects_anonymous(client):
    """Anonymous visitors are redirected from dashboard to login."""
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_change_password(auth_client, student_user, db):
    """Student can change password with valid current password."""
    res = auth_client.post("/auth/profile", data={
        "current_password": "StudentPass123!",
        "new_password": "NewSecretPass456!",
        "confirm_password": "NewSecretPass456!",
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Password updated successfully" in res.data
    # Verify new password works
    db.session.refresh(student_user)
    assert student_user.check_password("NewSecretPass456!")


def test_delete_account(auth_client, student_user, db):
    """Student can self-delete their account and associated data."""
    user_id = student_user.id
    res = auth_client.post("/auth/delete-account", follow_redirects=True)
    assert res.status_code == 200
    assert b"permanently deleted" in res.data
    assert db.session.get(User, user_id) is None

