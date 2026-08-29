# Landlord–Tenant Direct Connect Platform

**Project title:** Design and Implementation of an Online Platform for Direct Landlord-to-Tenant Contact Using Artificial Intelligence and Machine Learning Techniques

## Project description

A web-based platform that enables direct interaction between landlords and prospective tenants. The system provides:

- apartment search and filtering;
- landlord registration and management of residential apartment listings;
- tenant apartment preferences;
- personalised apartment recommendations using **Weighted K-Nearest Neighbour (Weighted KNN)**;
- direct landlord–tenant messaging;
- administrative management of users, listings and the landlord-verification workflow.

This is an academic prototype. It is not a legal property-ownership verification platform, payment platform, tenancy-contract system, or commercial real-estate marketplace.

## Scope and methodology

- **Development methodology:** Agile (incremental, tested, verifiable phases).
- **Analysis/design approach:** Object-Oriented Analysis and Design (OOAD).
- Authoritative project rules: `AGENTS.md`.
- Authoritative specification: `SYSTEM_REQUIREMENTS.md`.
- Technology/implementation plan: `TECH_STACK_AND_IMPLEMENTATION_PLAN.md`.

## Technology stack

- **Backend:** Python 3.13.15, Django 6.1, Django REST Framework 3.18
- **Database:** PostgreSQL 18
- **Frontend:** HTML5, CSS3, JavaScript, Django Templates, Bootstrap 5
- **Machine learning:** Weighted KNN with feature weighting (NumPy / pandas / scikit-learn for preprocessing & metrics only)
- **Environment:** Python virtual environment (`.venv`), environment variables
- **Production:** Gunicorn + WhiteNoise (+ Nginx/Render), PostgreSQL, HTTPS

See `TECH_STACK_AND_IMPLEMENTATION_PLAN.md` §E for the full approved stack.

## Project structure

```
landlord_tenant_project/
├── manage.py
├── .env                    (never committed)
├── .env.example
├── .gitignore
├── README.md
├── AGENTS.md
├── SYSTEM_REQUIREMENTS.md
├── TECH_STACK_AND_IMPLEMENTATION_PLAN.md
├── requirements.txt
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── apartments/
│   ├── recommendations/
│   ├── messaging/
│   └── verification/
├── api/
│   ├── urls.py
│   └── v1/
├── ml/
│   ├── __init__.py
│   ├── features.py
│   ├── preprocessing.py
│   ├── weighted_knn.py
│   ├── ranking.py
│   └── evaluation.py
├── templates/
│   ├── base.html
│   ├── home.html
│   └── about.html
├── static/
│   ├── css/
│   └── vendor/           (Bootstrap 5 + icons, local)
├── media/
├── staticfiles/
└── tests/
    ├── unit/
    ├── integration/
    ├── api/
    └── ml/
```

## Installation (local development)

The project foundation (Sprints 1.1–1.3) is set up. Steps below reflect the current, working setup.

1. Clone the repository and move into the project directory.
2. Create and activate the virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure environment variables (see below).
   Ensure `.env` contains the PostgreSQL `DATABASE_USER`, `DATABASE_PASSWORD`,
   and `DATABASE_NAME` values so the Django development server can connect to
   `landlord_tenant_db`.

## Environment setup

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Fill in real values in `.env`:
   - `SECRET_KEY` — a strong random value (development can also auto-generate);
   - `DATABASE_USER` and `DATABASE_PASSWORD` — your PostgreSQL credentials;
   - leave `DEBUG=True` for local development only; use `False` in production.

Never commit `.env`. Use `.env.example` as the template without real credentials.

## Database setup

Development database: `landlord_tenant_db` (PostgreSQL, host `127.0.0.1:5432`).
Connection values are supplied exclusively through `.env` (see `.env.example`).

The Django-to-PostgreSQL connection is verified; Django's built-in migrations
(admin, auth, contenttypes, sessions) are applied.

## Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Development commands

```powershell
python manage.py runserver
python manage.py check
python manage.py check --deploy   # production security check
```

## Testing commands

```powershell
python manage.py test
# or with pytest once configured
pytest
```

## Machine-learning recommendation

The recommendation component uses **Weighted K-Nearest Neighbour (Weighted KNN)** with feature weighting.

- Tenant preferences form the query vector `U = (u1, ..., un)`.
- Apartment characteristics form candidate vectors `A = (a1, ..., an)`.
- Weighted Euclidean distance: `Dw(U,A) = sqrt( Σ wi(ui − ai)^2 )`.
- Lower distance → greater similarity → higher recommendation rank.
- Mandatory/hard filters are applied before ML ranking.
- `K` is configurable (initial `K = 5`).
- Min–Max normalisation is used for numerical features, with protection against division-by-zero.

The recommendation engine will operate on actual apartment records stored in the database. No fabricated scores or results are used.

## Deployment

> Production configuration and deployment are handled in later phases. Approved target: Render with managed PostgreSQL, Gunicorn, WhiteNoise, HTTPS; Nginx as the documented self-hosted alternative.

## Current development status

Phase 1 (Project Foundation and Environment) is complete.
- **Sprint 1.1 (completed):** Development environment verified.
- **Sprint 1.2 (completed):** Project and repository initialisation (Git, `.gitignore`, `.env.example`, README, branch strategy).
- **Sprint 1.3 (completed):** Django project initialisation — virtual environment, approved dependencies installed and pinned, `config/` settings split (`base`, `development`, `production`), modular apps under `apps/`, base URL routing, `ml/`/`api/`/`tests/` structure, foundation tests.
- **Sprint 1.4 (completed):** PostgreSQL integration — `.env` credentials, Django connected to `landlord_tenant_db`, migrations applied, connectivity and `runserver` verified.
- **Sprint 1.5 (completed):** Base UI and static/media foundation — `base.html` (Bootstrap 5 navbar + footer, brand **Landlord-Tenant Connect**, blocks for title/content/extra assets), `home.html` and `about.html` extend the base template; localized Bootstrap 5.3.3 + Bootstrap Icons vendored under `static/vendor/`; `css/main.css`; development static/media serving in `config/urls.py`; `collectstatic` verified (163 files). Foundation suite now 12 tests (settings, routing, base UI rendering). Home, About, static assets served over HTTP (200).

Foundation (Phase 1) is complete.

Phase 2 (Authentication and User Management) is in progress.
- **Sprint 2.1 (completed):** Custom User model and roles — email-based custom
  `User` model (`AUTH_USER_MODEL = "accounts.User"`) with TENANT / LANDLORD /
  ADMIN roles, `full_name` and `phone` profile fields, custom `UserManager`
  (email authentication, superuser creation), role helper properties
  (`is_tenant`, `is_landlord`, `is_admin`), registered in Django Admin,
  migration `accounts.0001_initial` applied, Role-enabled user model.
- **Sprint 2.2 (completed):** Registration — public `POST /api/v1/auth/register/`
  endpoint registering TENANT and LANDLORD accounts. Includes email format and
  duplicate-account prevention, Django password validation, role restriction
  (ADMIN rejected — created administratively only), password hashing, and a
  consistent `success/message/data` response envelope. 9 registration API tests.
- **Sprint 2.3 (completed):** Authentication — JWT login (`POST
  /api/v1/auth/login/`) returning access (60 min) and refresh (1 day) tokens,
  `POST /api/v1/auth/refresh/` to mint a fresh access token, server-side logout
  (`POST /api/v1/auth/logout/`) that blacklists the refresh token via SimpleJWT
  `token_blacklist`, and a protected `GET /api/v1/auth/me/` profile endpoint.
  `REST_FRAMEWORK` defaults to JWT + `IsAuthenticated`; `SIMPLE_JWT` configured
  (60-min access, no rotation/blacklist-after-rotation). Invalid/blacklisted
  tokens return clean 401 responses. 9 authentication API tests (44 total).
- **Sprint 2.4 (completed):** Profile management — the protected `GET/PATCH
  /api/v1/auth/me/` endpoint now supports viewing (`GET`) and editing
  (`PATCH`) the authenticated user's own profile. Contact information
  (`full_name`, `phone`) is editable for both TENANT and LANDLORD roles;
  identity fields (email, role, is_active) are read-only and cannot be changed
  by the user. Uses a `ProfileSerializer` (ModelSerializer) with server-side
  validation. 7 profile API tests (51 total).

Features (apartments, recommendations, messaging, verification,
administration) are not yet implemented.
