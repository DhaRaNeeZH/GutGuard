"""Catalogue blueprint."""
from flask import Blueprint

catalogue_bp = Blueprint("catalogue", __name__)

from . import routes  # noqa: F401, E402
