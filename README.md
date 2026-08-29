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

- **Backend:** Python 3.13.x, Django, Django REST Framework
- **Database:** PostgreSQL
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
├── static/
├── media/
├── staticfiles/
└── tests/
    ├── unit/
    ├── integration/
    ├── api/
    └── ml/
```

## Installation (local development)

> Detailed setup instructions will be completed in later Phase 1 sprints (Django initialisation and PostgreSQL integration). The milestones below reflect the approved plan.

1. Clone the repository and move into the project directory.
2. Create and activate the virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies (list to be finalised in Sprint 1.3):
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure environment variables (see below).

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

> PostgreSQL integration is completed in Sprint 1.4. Expected development database: `landlord_tenant_db` (host `127.0.0.1:5432`).

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

Phase 1 (Project Foundation and Environment) is in progress.
- **Sprint 1.1 (completed):** Development environment verified.
- **Sprint 1.2 (current):** Project and repository initialisation (Git, `.gitignore`, `.env.example`, README).
- Sprints 1.3–1.5: Django project initialisation, PostgreSQL integration, base UI/static/files foundation.

Nothing beyond the repository foundation has been implemented yet.
