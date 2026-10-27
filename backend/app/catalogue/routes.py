"""Catalogue routes – food search API and browse."""
from flask import jsonify, request, render_template
from flask_login import login_required
from sqlalchemy import or_

from . import catalogue_bp
try:
    from backend.extensions import db
    from database.models import FoodCatalogue, FoodAlias, FoodCategory
except ImportError:
    from extensions import db
    from models import FoodCatalogue, FoodAlias, FoodCategory


@catalogue_bp.route("/search")
@login_required
def search():
    """
    JSON autocomplete endpoint.
    GET /catalogue/search?q=idli&limit=10
    Returns: [{id, name, category, region, is_vegetarian}, ...]
    """
    query  = request.args.get("q", "").strip().lower()
    limit  = min(int(request.args.get("limit", 15)), 50)
    cat_id = request.args.get("category_id", type=int)

    if len(query) < 1:
        return jsonify([])

    # Build filter: match on normalized name OR alias
    name_match  = FoodCatalogue.name_normalized.contains(query)
    alias_match = FoodCatalogue.id.in_(
        db.session.query(FoodAlias.food_id)
        .filter(FoodAlias.alias_normalized.contains(query))
    )
    base_q = (
        FoodCatalogue.query
        .filter(FoodCatalogue.status == "active")
        .filter(or_(name_match, alias_match))
    )

    if cat_id:
        base_q = base_q.filter(FoodCatalogue.category_id == cat_id)

    foods = base_q.order_by(FoodCatalogue.name).limit(limit).all()

    return jsonify([
        {
            "id":            f.id,
            "name":          f.name,
            "category":      f.category.name if f.category else None,
            "region":        f.region,
            "is_vegetarian": f.is_vegetarian,
        }
        for f in foods
    ])


@catalogue_bp.route("/browse")
@login_required
def browse():
    """Browse the food catalogue by category."""
    categories = FoodCategory.query.order_by(FoodCategory.sort_order, FoodCategory.name).all()
    selected_cat = request.args.get("category_id", type=int)
    query_str = request.args.get("q", "").strip()

    foods_q = FoodCatalogue.query.filter(FoodCatalogue.status == "active")
    if selected_cat:
        foods_q = foods_q.filter(FoodCatalogue.category_id == selected_cat)
    if query_str:
        foods_q = foods_q.filter(
            FoodCatalogue.name_normalized.contains(query_str.lower())
        )
    foods = foods_q.order_by(FoodCatalogue.name).limit(100).all()

    return render_template(
        "catalogue/browse.html",
        categories=categories,
        foods=foods,
        selected_cat=selected_cat,
        query_str=query_str,
    )
