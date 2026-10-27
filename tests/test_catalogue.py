"""
Tests for food catalogue browsing, filtering, search, and JSON autocomplete API.
"""
from database.models import FoodCatalogue, FoodAlias, FoodCategory


def test_catalogue_browse_page(auth_client):
    """Authenticated student can view catalogue page."""
    res = auth_client.get("/catalogue/browse")
    assert res.status_code == 200
    assert b"Campus Food Catalogue" in res.data
    assert b"Idli" in res.data
    assert b"Dosa" in res.data


def test_catalogue_category_filter(auth_client, db):
    """Filtering by category shows only items in that category."""
    other_cat = FoodCategory(name="Beverages", sort_order=2)
    db.session.add(other_cat)
    db.session.flush()

    tea = FoodCatalogue(
        name="Chai",
        name_normalized="chai",
        category_id=other_cat.id,
        is_vegetarian=True,
        status="active",
        is_verified=True,
    )
    db.session.add(tea)
    db.session.commit()

    res = auth_client.get(f"/catalogue/browse?category_id={other_cat.id}")
    assert res.status_code == 200
    assert b"Chai" in res.data
    assert b"Idli" not in res.data


def test_catalogue_search_api_name(auth_client):
    """JSON autocomplete search finds matching food by name."""
    res = auth_client.get("/catalogue/search?q=idl")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Idli"
    assert data[0]["is_vegetarian"] is True


def test_catalogue_search_api_empty_query(auth_client):
    """Empty query returns empty JSON list without error."""
    res = auth_client.get("/catalogue/search?q=")
    assert res.status_code == 200
    assert res.get_json() == []


def test_catalogue_search_api_alias(auth_client, db):
    """Search matches aliases (e.g. 'steam idli' -> 'Idli')."""
    idli = FoodCatalogue.query.filter_by(name="Idli").first()
    alias = FoodAlias(
        food_id=idli.id,
        alias="Steam Idli",
        alias_normalized="steam idli",
    )
    db.session.add(alias)
    db.session.commit()

    res = auth_client.get("/catalogue/search?q=steam")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Idli"
