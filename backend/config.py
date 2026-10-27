"""
GutGuard – Application Configuration
Reads sensitive values from environment variables.
Never hardcode secrets here.
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(basedir, ".env"))  # Load root .env file if present

class Config:
    # ── Security ──────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # ── Database ──────────────────────────────────────────
    DB_HOST     = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT     = os.environ.get("DB_PORT", "3306")
    DB_NAME     = os.environ.get("DB_NAME", "gutguard")
    DB_USER     = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    USE_SQLITE  = os.environ.get("USE_SQLITE", "true").lower() in ("true", "1", "yes")

    # Determine database URI:
    # 1. Explicit DATABASE_URL
    # 2. SQLite if USE_SQLITE=true
    # 3. Default to MySQL
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url:
        SQLALCHEMY_DATABASE_URI = _db_url
    elif USE_SQLITE:
        _db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database", "gutguard.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        )

    # Engine options: SQLite does not use pool_recycle / pool_size
    if "sqlite" in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size":     10,
            "pool_recycle":  3600,
            "pool_pre_ping": True,   # Reconnect on stale connections
            "pool_timeout":  10,
        }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session / Cookies ─────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14   # 14 days

    # ── Application ───────────────────────────────────────
    ITEMS_PER_PAGE          = 20
    MAX_CUSTOM_FOODS_REVIEW = 100   # Admin queue size
    WATER_DEFAULT_UNIT      = "ml"

    # ── Admin bootstrap ───────────────────────────────────
    ADMIN_EMAIL    = os.environ.get("ADMIN_EMAIL", "admin@gutguard.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")


class DevelopmentConfig(Config):
    DEBUG = True
    # Show SQL queries in development
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Default config used when no FLASK_ENV is set
config_map = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}

def get_config(config_name=None):
    if config_name and config_name in config_map:
        return config_map[config_name]
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)

