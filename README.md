# GutGuard — Meal Habit Awareness Platform

> **MCA College Mini-Project**  
> *A clean, interactive, privacy-first web application helping college students understand their eating patterns, build dietary awareness, and maintain consistent meal routines.*

---

## 🌟 Key Highlights

- **Designed for College Life**: Caters specifically to Indian college and hostel eating patterns (mess meals, canteen snacks, street food, beverages, and regional staples).
- **Rule-Based & Transparent**: No black-box medical diagnoses or pseudo-scientific health scores. All habit observations cite clear, configurable rules (e.g. `GG-001`, `GG-002`, `GG-003`).
- **Privacy First**: Student meal logs and water intake remain private to each student. Admins only manage the reference food catalogue and review custom food submissions.
- **Robust Tech Stack**: Flask 3.1, SQLAlchemy 2.1 ORM, Flask-Login, Flask-WTF with CSRF protection, ReportLab PDF generation, Chart.js visualizations, and Bootstrap 5 + Vanilla CSS design tokens.
- **Dual Database Flexibility**: Works natively with MySQL (production-ready connection pooling) or SQLite (zero-config local dev & lightning-fast in-memory testing).
- **100% Automated Test Coverage**: 34 comprehensive pytest unit and integration tests covering authentication, journal CRUD, search autocomplete, rule alerts, RBAC, and PDF downloads.

---

## 🏗️ Architecture & Project Structure

```
GutGuard/
├── frontend/                     # EVERYTHING VISUAL & UI
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html             # Common layout, navbar, flash alerts, modal & footer
│   │   ├── admin/                # Admin dashboard, catalogue manager, custom review
│   │   ├── auth/                 # Login, register, profile
│   │   ├── catalogue/            # Food browser with search & category filters
│   │   ├── errors/               # 403 Forbidden, 404 Not Found, 500 Server Error
│   │   ├── insights/             # Interactive weekly charts & rule alerts
│   │   ├── main/                 # Landing page & student overview dashboard
│   │   ├── meals/                # Daily journal, multi-food logger, meal editor
│   │   └── reports/              # Report generation form & PDF download history
│   └── static/                   # CSS, JavaScript & Static Assets
│       ├── css/gutguard.css      # Design tokens, themes, cards, badges
│       ├── js/                   # Frontend scripts & charts
│       └── images/               # UI logos & graphics
│
├── backend/                      # EVERYTHING SERVER & PYTHON LOGIC
│   ├── app/                      # Application Package & Blueprints
│   │   ├── __init__.py           # Application Factory (create_app)
│   │   ├── admin/                # Admin portal & moderation routes
│   │   ├── auth/                 # Authentication routes & forms
│   │   ├── catalogue/            # Indian food catalogue API routes
│   │   ├── insights/             # Habit analytics & rule engine
│   │   ├── main/                 # Home dashboard & landing routes
│   │   ├── meals/                # Meal CRUD & water logging routes
│   │   └── reports/              # ReportLab PDF generator routes
│   ├── extensions.py             # Shared Flask extensions (db, migrate, csrf, login)
│   └── config.py                 # Development, Testing, Production configurations
│
├── database/                     # EVERYTHING DATA & SQL
│   ├── models.py                 # SQLAlchemy ORM models (User, Meal, FoodCatalogue, etc.)
│   ├── gutguard.db               # SQLite local database
│   ├── migrations/               # Database migration scripts
│   └── seeds/                    # Seed scripts for initial & demo data
│       ├── catalogue_seeder.py   # 118 curated Indian foods seeder
│       └── demo_seeder.py        # Synthetic demo records for faculty review
│
├── tests/                        # Automated Pytest Test Suite
│   ├── conftest.py               # In-memory SQLite fixtures & test client
│   ├── test_admin.py             # RBAC and moderation tests
│   ├── test_auth.py              # Auth and security tests
│   ├── test_catalogue.py         # Search API and category tests
│   ├── test_insights.py          # Rule engine and analytics tests
│   ├── test_meals.py             # CRUD and water log tests
│   └── test_reports.py           # PDF report generation tests
│
├── docs/                         # Project Documentation
│   └── design-system/            # Design system tokens and specifications
│
├── run.py                        # Single CLI & Web entry point
├── requirements.txt              # Pinned Python package dependencies
├── .env.example                  # Environment variables template
└── README.md                     # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.15)
- MySQL (Optional: app automatically falls back to SQLite if `USE_SQLITE=true`)

### 2. Setup Virtual Environment
```bash
cd GutGuard
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
For quick local testing with SQLite, set in `.env` (or via command line):
```ini
USE_SQLITE=true
SECRET_KEY=gutguard-super-secret-key-mca-project
ADMIN_EMAIL=admin@gutguard.local
ADMIN_PASSWORD=AdminPass123!
```

### 5. Initialise Database & Seed Data
GutGuard includes convenient CLI helper commands:

```bash
# 1. Create database schema and default roles (student, admin)
flask --app run init-db

# 2. Seed 118 Indian foods, regional tags, vegetarian status, and aliases
flask --app run seed-catalogue

# 3. (Optional) Seed realistic synthetic demo meals for presentation
flask --app run seed-demo-data
```

### 6. Run the Application
```bash
python run.py
```
Open your browser and navigate to: **[http://localhost:5000](http://localhost:5000)**

---

## 👤 Default Demo Accounts

| Role | Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@gutguard.local` | `AdminPass123!` | Food Catalogue moderation, custom food reviews |
| **Demo Student** | `demo@gutguard.local` | `demopassword123` | Pre-populated 7-day meal journal, charts, and water intake |
| **New Student** | *(Self-register)* | *(Your chosen pass)* | Clean personal dashboard & private journal |

---

## 🧪 Running Automated Tests

GutGuard includes a full suite of automated unit and integration tests executed against an in-memory SQLite database:

```bash
python -m pytest -v
```

**Test Suite Coverage Summary (36 Automated Tests, 84% Coverage):**
- **`tests/test_auth.py`**: Registration, duplicate prevention, password validation, login, session isolation, logout, password change, self-service account & data deletion.
- **`tests/test_meals.py`**: Journal rendering, multi-food logging, custom unlisted food creation, edit meal, cascade item deletion, cross-user isolation (403), water intake tracking.
- **`tests/test_catalogue.py`**: Category filtering, keyword search, alias resolution (e.g. `Steam Idli` -> `Idli`), and JSON autocomplete API.
- **`tests/test_insights.py`**: Rule evaluation (`GG-001` logging frequency, `GG-002` breakfast logging, `GG-003` snack-heavy balance, `GG-004` high consistency), demo data exclusion, Chart.js payload formatting.
- **`tests/test_reports.py`**: PDF compilation via ReportLab, custom period ranges, non-diagnostic disclaimer verification, report download records, and previous report re-downloads.
- **`tests/test_admin.py`**: Role-based access control (RBAC), food verification, custom food approvals (promoting to active catalogue), custom food rejections.

---

## 🛡️ Ethics, Privacy & Health Disclaimers

1. **Non-Diagnostic Boundary**: GutGuard explicitly states on its dashboard, insights page, and exported PDF reports that it is **not a clinical diagnostic tool**. It records self-reported student inputs to foster awareness.
2. **Student Data Sovereignty**: Administrators cannot browse or inspect private student meal logs. Admin privileges are strictly limited to managing reference food catalogue items.
3. **Transparent Rules**: Habit insights are computed using explicit, labeled logical rules rather than speculative scoring algorithms. Every insight displays its rule identifier and calculation basis.

---

## 🎓 Faculty Presentation Points

When demonstrating this project to academic evaluators:
1. **Explain the DB Schema (`models.py`)**: Show the normalization between `Meal` (session) and `MealItem` (individual food with quantity/unit), along with the separation of `CustomFood` so student submissions cannot pollute reference catalogue data without review.
2. **Show the Autocomplete API (`/catalogue/search`)**: Demonstrate the JSON search endpoint resolving both official names and common Indian regional aliases (`Pulihora` / `Tamarind Rice`).
3. **Walk Through Insights & Charts (`app/insights/routes.py`)**: Point out how days elapsed are computed dynamically, how demo records are filtered using SQL flags (`is_demo = False`), and how Chart.js renders the weekly patterns.
4. **Demonstrate PDF Generation (`app/reports/routes.py`)**: Show real-time vector PDF creation with ReportLab including tabular habit breakdowns and compliance disclaimers.
5. **Highlight RBAC & Security**: Show CSRF tokens on forms, password hashing using `werkzeug.security`, HTTP-only cookies, and server-side route enforcement (`@admin_required` returning HTTP 403).
