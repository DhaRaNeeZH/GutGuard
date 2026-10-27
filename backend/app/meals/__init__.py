"""Meals blueprint."""
from flask import Blueprint

meals_bp = Blueprint("meals", __name__)

from . import routes  # noqa: F401, E402
