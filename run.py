"""GutGuard – Entry point."""
import sys
import os
from pathlib import Path

# Auto-use the project virtual environment if run with system python
BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if VENV_PYTHON.exists() and os.path.normcase(sys.executable) != os.path.normcase(str(VENV_PYTHON)):
    import subprocess
    sys.exit(subprocess.call([str(VENV_PYTHON)] + sys.argv))

# Add project root, backend, and database to sys.path so modules can be imported smoothly
for p in (BASE_DIR, BASE_DIR / "backend", BASE_DIR / "database"):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

from backend.app import create_app
from backend.extensions import db
from database.models import Role, User

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Create all tables and seed essential data (roles, admin user)."""
    from backend.config import get_config
    cfg = get_config()

    with app.app_context():
        db.create_all()

        # Seed roles
        for role_name in ("student", "admin"):
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

        # Seed admin user
        admin_email = cfg.ADMIN_EMAIL
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_role = Role.query.filter_by(name="admin").first()
            admin = User(
                email=admin_email,
                display_name="GutGuard Admin",
                role=admin_role,
            )
            admin.set_password(cfg.ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print(f"[init-db] Admin user created: {admin_email}")
        else:
            admin.set_password(cfg.ADMIN_PASSWORD)
            db.session.commit()
            print(f"[init-db] Admin user updated with current credentials: {admin_email}")

        print("[init-db] Database initialised successfully.")


@app.cli.command("seed-catalogue")
def seed_catalogue():
    """Seed the Indian food catalogue with initial data."""
    from database.seeds.catalogue_seeder import seed_initial_catalogue
    with app.app_context():
        seed_initial_catalogue()
        print("[seed-catalogue] Catalogue seeded.")


@app.cli.command("seed-demo-data")
def seed_demo():
    """Create clearly-labelled demo/test meal records for development."""
    from database.seeds.demo_seeder import seed_demo_meals
    with app.app_context():
        seed_demo_meals()
        print("[seed-demo-data] Demo meals seeded.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.cli()
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
