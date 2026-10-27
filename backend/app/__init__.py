"""
GutGuard – Application Factory
Creates and configures the Flask app, registers extensions and blueprints.
"""
import os
from pathlib import Path
from flask import Flask, render_template
from datetime import timedelta, date as _date, datetime as _datetime

try:
    from backend.config import get_config
    from backend.extensions import db, migrate, login_manager, csrf
    from database.models import User
except ImportError:
    from config import get_config
    from extensions import db, migrate, login_manager, csrf
    from models import User

# Paths for frontend templates and static assets
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = str(ROOT_DIR / "frontend" / "templates")
STATIC_DIR = str(ROOT_DIR / "frontend" / "static")


def create_app(config_name=None) -> Flask:
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR
    )
    if isinstance(config_name, str) or config_name is None:
        app.config.from_object(get_config(config_name))
    else:
        app.config.from_object(config_name)

    # ── Jinja2 template globals ───────────────────────────
    # NOTE: use callables so each request gets a fresh value.
    app.jinja_env.globals.update(
        timedelta=timedelta,
        today=_date.today,       # callable – templates call today() for current date
        date=_date,
        datetime=_datetime,
        now=_datetime.now,       # callable – templates call now() for current datetime
    )

    # ── Extensions ────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Flask-Login user loader ────────────────────────────
    @login_manager.user_loader
    def load_user(user_id: str) -> "User | None":
        return db.session.get(User, int(user_id))

    # ── Blueprints ────────────────────────────────────────
    from .auth.routes      import auth_bp
    from .meals.routes     import meals_bp
    from .catalogue.routes import catalogue_bp
    from .insights.routes  import insights_bp
    from .reports.routes   import reports_bp
    from .admin.routes     import admin_bp
    from .main.routes      import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(meals_bp,     url_prefix="/meals")
    app.register_blueprint(catalogue_bp, url_prefix="/catalogue")
    app.register_blueprint(insights_bp,  url_prefix="/insights")
    app.register_blueprint(reports_bp,   url_prefix="/reports")
    app.register_blueprint(admin_bp,     url_prefix="/admin")

    # ── Error handlers ────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        # Do NOT expose stack traces
        app.logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500

    return app
