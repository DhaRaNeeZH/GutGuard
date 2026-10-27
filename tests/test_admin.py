"""
Tests for admin portal, role protection (RBAC), catalogue management, and custom food moderation.
"""
from database.models import FoodCatalogue, CustomFood, Role, User


def test_student_forbidden_from_admin(auth_client):
    """Students receive 403 Forbidden when attempting to access admin routes."""
    res = auth_client.get("/admin/")
    assert res.status_code == 403

    res_cat = auth_client.get("/admin/catalogue")
    assert res_cat.status_code == 403

    res_custom = auth_client.get("/admin/custom-foods")
    assert res_custom.status_code == 403


def test_anonymous_redirected_from_admin(client):
    """Unauthenticated users are redirected to login."""
    res = client.get("/admin/")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_admin_dashboard(admin_client):
    """Admin dashboard loads summary metrics."""
    res = admin_client.get("/admin/")
    assert res.status_code == 200
    assert b"Admin Dashboard" in res.data
    assert b"Active Foods" in res.data


def test_admin_catalogue_list_and_verify(admin_client, db):
    """Admin can view catalogue and verify unverified foods."""
    unverified = FoodCatalogue(
        name="Cold Coffee",
        name_normalized="cold coffee",
        status="active",
        is_verified=False,
    )
    db.session.add(unverified)
    db.session.commit()

    res = admin_client.get("/admin/catalogue")
    assert res.status_code == 200
    assert b"Cold Coffee" in res.data

    verify_res = admin_client.post(f"/admin/catalogue/{unverified.id}/verify", follow_redirects=True)
    assert verify_res.status_code == 200
    assert b"marked as verified" in verify_res.data
    db.session.refresh(unverified)
    assert unverified.is_verified is True


def test_admin_approve_custom_food(admin_client, student_user, db):
    """Admin approves custom food submission and promotes it to FoodCatalogue."""
    custom = CustomFood(
        submitted_by_id=student_user.id,
        name="Millet Khichdi",
        name_normalized="millet khichdi",
        review_status="pending",
    )
    db.session.add(custom)
    db.session.commit()

    res = admin_client.post(f"/admin/custom-foods/{custom.id}/approve", follow_redirects=True)
    assert res.status_code == 200
    assert b"added to catalogue" in res.data

    db.session.refresh(custom)
    assert custom.review_status == "approved"
    assert custom.catalogue_food_id is not None

    promoted = db.session.get(FoodCatalogue, custom.catalogue_food_id)
    assert promoted is not None
    assert promoted.name == "Millet Khichdi"
    assert promoted.is_verified is True


def test_admin_reject_custom_food(admin_client, student_user, db):
    """Admin can reject improper custom food submission."""
    custom = CustomFood(
        submitted_by_id=student_user.id,
        name="Random Junk 123",
        name_normalized="random junk 123",
        review_status="pending",
    )
    db.session.add(custom)
    db.session.commit()

    res = admin_client.post(f"/admin/custom-foods/{custom.id}/reject", follow_redirects=True)
    assert res.status_code == 200
    assert b"rejected" in res.data

    db.session.refresh(custom)
    assert custom.review_status == "rejected"
    assert custom.catalogue_food_id is None
