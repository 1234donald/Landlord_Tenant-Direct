# TECH STACK AND IMPLEMENTATION PLAN

**Project:** Design and Implementation of an Online Platform for Direct Landlord-to-Tenant Contact Using Artificial Intelligence and Machine Learning Techniques

**System Name:** Landlord–Tenant Direct Connect Platform

**Stage:** Analysis Only — No application code written or modified.

**Basis:** This document is derived strictly from `AGENTS.md` and `SYSTEM REQUIREMENTS AND ARCHITECTURE SPECIFICATION.md`. Every proposed technology has been verified against these two documents before inclusion. Any item not explicitly allowed or that conflicts with the approved scope has been either excluded or flagged for approval.

---

## A. Project Overview

The platform is a web-based system that:

1. Lets prospective tenants search for and filter residential apartments.
2. Lets landlords register, manage profiles, submit verification information, and create/manage apartment listings with images.
3. Lets tenants and landlords communicate directly through a messaging system.
4. Lets administrators manage users, landlords, apartments, and the landlord-verification workflow.
5. Provides personalised apartment recommendations using **Weighted K-Nearest Neighbour (Weighted KNN)** with feature weighting.

**Methodology:**
- Development methodology: **Agile** (incremental, tested, verifiable phases).
- System analysis/design approach: **Object-Oriented Analysis and Design (OOAD)**.
- These are two distinct things: Agile is the *development methodology*; OOAD is the *analysis/design approach*.

**Key constraints (non-negotiable):**
- Backend: Python + Django.
- API: Django REST Framework where required.
- DB: PostgreSQL.
- Frontend: HTML5/CSS3/JavaScript + Django Templates + Bootstrap 5 (no React).
- ML: Weighted KNN with feature weighting — must **not** be replaced by collaborative filtering, deep learning, hybrid, or external recommender.
- The system is an **administrative platform control** for verification; it does **not** perform legal verification or property-ownership determination.

---

## B. Requirements Analysis

### B.1 Functional Requirements (FR)

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | User registration (Tenant, Landlord) | Admin accounts created administratively, not by public registration |
| FR-002 | Authentication (login, logout, password hashing, validation, token auth, session management, password reset) | API uses **JWT** |
| FR-003 | Tenant profile management | Update own profile |
| FR-004 | Apartment search | Location, min/max price, type, bedrooms, bathrooms, facilities, availability |
| FR-005 | Apartment filtering | Hard/mandatory filters applied before ML ranking |
| FR-006 | Apartment details view | Public viewable |
| FR-007 | Tenant preference entry/management | Stored in PostgreSQL |
| FR-008 | Recommendation generation & viewing | Weighted KNN |
| FR-009 | Messaging (send/receive, conversations, status, history, timestamps) | No WebSockets in V1 unless proven necessary |
| FR-010 | Landlord registration + profile management | |
| FR-011 | Landlord verification submission + status | Administrative review workflow |
| FR-012 | Landlord apartment CRUD + image upload + availability | Validation required |
| FR-013 | Administrator: manage users/landlords/apartments | |
| FR-014 | Administrator: review/approve/reject verification | |
| FR-015 | Administrator: system monitoring, reports, activity | |
| FR-016 | API documentation | OpenAPI via drf-spectacular |

### B.2 Non-Functional Requirements (NFR)

| Category | Requirement |
|----------|-------------|
| Performance | Normal API requests target < 2 seconds under normal dev/test load; recommendation generation measured separately |
| Availability | Available whenever the hosting service is operational |
| Scalability | Support more apartments, tenants, landlords, recommendations, API requests without full redesign |
| Maintainability | PEP 8, modular architecture, separation of concerns, reusable services, documented APIs, automated tests, Git version control |
| Security | Password hashing, JWT, RBAC, CSRF, input validation, ORM-based SQLi protection, XSS protection, secure cookies, HTTPS, env vars, secret management, upload validation, throttling |
| Usability | Responsive, simple, accessible, consistent, professional |

### B.3 ML Requirements

- **Algorithm:** Weighted KNN with feature weighting (mandatory/non-negotiable).
- **Pipeline:** Input validation → Mandatory filtering → Candidate apartments → Feature extraction → Categorical encoding → Numerical normalisation → Feature weighting → Weighted distance → K nearest → Ranking → Results.
- **Features:** rental price, location, apartment type, bedrooms, bathrooms, parking, electricity, water, security, furnished status, facilities.
- **Distance:** `Dw(U,A) = sqrt( Σ wi(ui − ai)^2 )` — lower distance = greater similarity.
- **Normalisation:** Min-Max `x' = (x−xmin)/(xmax−xmin)`; avoid division-by-zero.
- **K:** Configurable; initial K=5; evaluated in Chapter 4 testing.
- **Evaluation:** Precision@K, Recall@K, Hit Rate@K, NDCG@K + manually defined tenant-preference test scenarios.

---

## C. System Modules

Per the specification, the system is split into modular Django apps (Section 19, 20, 43).

| Module/App | Responsibility |
|-----------|----------------|
| `accounts` | Custom User model, roles, registration, authentication (JWT), profile management, permissions |
| `apartments` | Apartment listing model, apartment images, search, filtering, availability, landlord CRUD |
| `recommendations` | Tenant preferences, recommendation generation, storage of recommendation results |
| `messaging` | Conversations, messages, message status, history, timestamps |
| `verification` | Landlord verification submissions and administrative review workflow |
| `ml/` (library module) | `features.py`, `preprocessing.py`, `weighted_knn.py`, `ranking.py`, `evaluation.py` |
| `api/` (package) | Global API URL routing; `api/v1/` endpoint modules |
| `core` (support) | Shared utilities/helpers, base templates, home/about pages (implied by general structure in AGENTS.md) |

The `ml/` package is kept **outside** the Django apps to preserve separation between the recommendation component and the web/presentation layer, as required by AGENTS.md §6.

---

## D. Actors and Permissions

### D.1 Actors

| Actor | Role | Capabilities |
|-------|------|--------------|
| **Tenant** | TENANT | Register, login, manage profile, search/filter apartments, view details, enter/manage preferences, generate & view recommendations, contact landlord, send/receive messages |
| **Landlord** | LANDLORD | Register, login, manage profile, submit verification info, create/edit/delete listings, upload images, set availability, view & respond to tenant messages |
| **Administrator** | ADMIN | Login, manage users/landlords, review verification, approve/reject, manage/remove apartments, monitor system, view reports & activity |

### D.2 Permissions (RBAC)

Derived from AGENTS.md §8 and Specification §22:

| Permission Class | Description |
|------------------|-------------|
| `IsAuthenticated` | Any logged-in user for protected reads |
| `TenantPermission` | Restricts to TENANT role |
| `LandlordPermission` | Restricts to LANDLORD role |
| `AdminPermission` | Restricts to ADMIN role |
| `IsOwnerOrAdmin` | Row-level: object owner or admin only |

**Rules:**
- Landlord can only manage own apartments; admin may manage all.
- Tenant can only manage own preferences/recommendations.
- Admin manages verification approve/reject; **landlords cannot approve themselves**. (Spec §39.14)
- Every protected API endpoint must have explicit permission rules (Spec §22).
- Public endpoints: home, about, apartment listings, apartment details, login, register.

---

## E. Complete Technology Stack

| Layer | Technology | Version Range | Purpose | Where Used | Why Appropriate |
|-------|-----------|---------------|---------|------------|-----------------|
| OS (Dev) | Windows 11 | Current | Development host | Dev machine | Specified by spec §25, AGENTS.md §45 |
| Language | Python | 3.13.x | Backend + ML language | All backend/ML code | Mandated; ML libs (NumPy, pandas, scikit-learn) support it |
| Web Framework | Django | 6.1 (verify) | Web framework, ORM, auth, admin, templates | Full backend | Mandated by AGENTS.md §4 and spec §25 |
| REST API | Django REST Framework | Current stable | API layer, serializers, ViewSets, pagination, throttling | `api/v1/` | Mandated |
| Auth (API) | djangorestframework-simplejwt | Current stable | JWT token auth (access/refresh) | Auth endpoints | Spec requires JWT |
| DB | PostgreSQL | 18 (verify) | Production + dev database | Data layer | Mandated |
| DB Driver | psycopg[binary] | Current | PostgreSQL driver for Django | settings/DB | Required for Django+Postgres |
| ORM | Django ORM | via Django | Data access, migrations | Models | Mandated; SQLi protection |
| ML | NumPy | Current | Array/numerical ops for KNN | `ml/` | Spec requires |
| ML | pandas | Current | Data frames for feature processing | `ml/` | Spec requires |
| ML | scikit-learn | Current | Preprocessing utilities (e.g. MinMaxScaler), metrics (precision@K, NDCG) | `ml/` | Spec requires; validators/metrics appropriate for Weighted KNN |
| Filtering | django-filter | Current | QuerySet filtering for search/filter APIs | `apartments` API | Spec §25 requires |
| Frontend | HTML5/CSS3/JS | — | Web UI | `templates/`, `static/` | Mandated |
| UI Kit | Bootstrap 5 | 5.x | Responsive styling/components | Templates | Spec §25 |
| Image processing | Pillow | Current | Validate/process apartment images | `apartments` | Spec requires |
| Env vars | python-dotenv | Current | Load `.env` locally | `manage.py`/settings | Spec requires |
| Static files | WhiteNoise | Current | Serve static in production | production settings | Spec §37 requires |
| API docs | drf-spectacular | Current | OpenAPI schema + Swagger UI | `api/` | Spec §25 requires |
| App server | Gunicorn | Current | Production WSGI server | production | Spec requires |
| Reverse proxy | Nginx | Current | TLS + proxy (self-hosted option) | production | AGENTS.md §44; spec §36 |
| Version control | Git | Current | Source control | repo | Mandated |
| Hosting | GitHub | — | Remote repository | repo | Mandated |
| Hosting (prod) | Render | — | Deploy Django web service + managed Postgres | production | Spec §37 |
| Testing | Django Test Framework + pytest + pytest-django | Current | Unit/integration/API tests | `tests/` | Spec §25, §32 |

> **NOTE:** Django 6.1 and PostgreSQL 18 are the versions stated in the specification. These must be **confirmed as available/stable** during Phase 1 environment verification. The actual installed versions will be pinned in `requirements.txt` after successful installation and testing (Spec §26). Python 3.13.x compatibility with Django must be verified at environment setup.

---

## F. Backend Architecture

**Layered architecture** (AGENTS.md §6):

- **Presentation layer:** Django Templates + Bootstrap 5 (server-rendered pages) and DRF API responses (JSON).
- **Application layer:** Django — Business Logic (services/views), DRF API, ML/Recommendation component.
- **Data layer:** PostgreSQL via Django ORM.

**Django project layout:**
- `config/` hold project settings split into `base.py`, `development.py`, `production.py`, plus `urls.py`, `asgi.py`, `wsgi.py`.
- Modular Django apps under `apps/`: `accounts`, `apartments`, `recommendations`, `messaging`, `verification`.
- `ml/` is a **pure-Python library package** (no Django coupling) so the recommender logic can be unit-tested independently.
- `api/` package routes `/api/v1/` endpoints.
- Business logic kept out of templates; recommendation algorithm kept out of views (AGENTS.md §6).

---

## G. Frontend Architecture

- **Public:** Home, About, Apartment Listings, Apartment Details, Login, Register.
- **Tenant:** Dashboard, Profile, Search, Filters, Apartment Details, Preferences, Recommendations, Messages.
- **Landlord:** Dashboard, Profile, Verification, My Apartments, Add/Edit Apartment, Apartment Details, Messages.
- **Administrator:** Dashboard, Users, Landlords, Verification, Apartments, Reports, System Activity.

**Implementation approach:** Django Templates rendered server-side where appropriate, with JS fetching/consuming the DRF JSON API where interactive (Spec §23: "frontend should communicate with the Django API where appropriate, while Django can also serve the main web interface"). **No React** — explicitly disallowed unless a specific requirement emerges.

---

## H. Database Architecture

**Database name:** `landlord_tenant_db` (local dev).

### H.1 Core Tables (entities)

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `users` | full name, email (unique), phone, password, role, timestamps | Custom User model; role = TENANT/LANDLORD/ADMIN. The role field (plus the profile fields) represents the "Tenant Profile" / "Landlord Profile"; there is no separate profile table. |
| `tenant_preferences` | FK tenant (→ users), preferred location, max price, type, bedrooms, bathrooms, parking, electricity, water, security, furnished, facilities, timestamps | For Weighted KNN query vector |
| `apartments` | FK landlord, title, description, location, area/address, rental price, type, bedrooms, bathrooms, parking, electricity, water, security, furnished, availability, timestamps | Validation: price positive numeric, counts numeric |
| `apartment_images` | FK apartment, image file, order, uploaded timestamp | Validated uploads |
| `recommendations` | FK tenant, FK apartment, distance, rank, k, algorithm, generated timestamp | Store results per spec §14 |
| `conversations` | participants, created timestamp | Messaging |
| `messages` | FK conversation, sender, recipient, body, status (sent/read), timestamp | |
| `landlord_verifications` | FK landlord, info submitted, status (pending/approved/rejected), reviewed-by admin, timestamps | |

### H.2 Relationships
- User (role = TENANT) → TenantPreference (1:N); `Preference.tenant` FK → `users`
- User (role = LANDLORD) → Apartment (1:N); `Apartment.landlord` FK → `users`
- Apartment → ApartmentImage (1:N)
- User[Tenant] → Recommendation → Apartment
- User[Tenant] ↔ User[Landlord] via Conversation/Message
- User[Landlord] → Verification ← User[Administrator]

### H.3 Constraints & Practices
- Primary keys, foreign keys, unique constraints (email), indexes on search fields (location, price, type), timestamps (created/updated).
- Users/roles enforced via custom User model and role field.
- Migrations via `makemigrations`/`migrate`; migration files committed (AGENTS.md §33).

---

## I. API Architecture

- **Framework:** Django REST Framework using serializers (validation) and ViewSets/routers (AGENTS §21).
- **Base URL:** `/api/v1/`
- **Consistent response envelope** (Spec §31): success (`success`, `message`, `data`) and error (`success`, `message`, `errors`); pagination via DRF (`count`, `next`, `previous`, `results`).

### I.1 Endpoints

**Auth** (`/api/v1/auth/`): register, login, refresh, logout, me (GET/PATCH)

**Users** (`/api/v1/users/`): list, retrieve, partial-update, delete (admin/owner)

**Apartments** (`/api/v1/apartments/`): list (filterable), create (landlord), retrieve, partial-update, delete

**Preferences** (`/api/v1/preferences/`): list, create, retrieve, partial-update, delete (tenant-owned)

**Recommendations** (`/api/v1/recommendations/`): `generate/` (POST), list (GET), retrieve (GET `{id}/`)

**Messages** (`/api/v1/messages/`): list, create, retrieve

**Conversations** (`/api/v1/conversations/`): list, retrieve, create message within conversation

**Verification** (`/api/v1/verification/`): submit, status

**Admin** (`/api/v1/admin/`): users, landlords, apartments, verifications (list + `{id}/approve/`, `{id}/reject/`), reports

### I.2 API Standards
JWT auth, HTTPS, permission classes, input serializers, throttling, pagination, filtering, error handling, consistent JSON (Spec §30).

---

## J. Authentication and Authorization

- **Stack:** Django Authentication + DRF + **JWT (SimpleJWT)** + Role-Based Permissions (Spec §22).
- **Custom User model** established early (Phase 2) to support role field and profile data (Spec §41 Phase 2 "Custom User").
- Roles: TENANT, LANDLORD, ADMIN.
- Permission classes: TenantPermission, LandlordPermission, AdminPermission, IsOwnerOrAdmin.
- Admin accounts created administratively (not via public registration) (FR-001).
- Password hashing via Django defaults; password validation on registration.
- API protected endpoints require valid JWT; refresh tokens supported.
- Throttling on auth endpoints (Spec §28).

---

## K. Weighted KNN Architecture

The recommendation component lives in `ml/` as a decoupled, pure-Python module, exposing a service callable from views.

**Module files (per spec §20):**
- `features.py` — build apartment + tenant-preference feature vectors.
- `preprocessing.py` — categorical encoding, Min-Max normalisation (with division-by-zero guard).
- `weighted_knn.py` — configurable K, weighted Euclidean distance `Dw(U,A) = sqrt(Σ wi(ui−ai)^2)`.
- `ranking.py` — ascending ranking by distance (lowest = best).
- `evaluation.py` — metrics: Precision@K, Recall@K, Hit Rate@K, NDCG@K.

**Pipeline (Spec §9):**
Tenant preferences → input validation → mandatory (hard) filtering → candidate apartments → feature extraction → categorical encoding → numerical normalisation → feature weighting → weighted distance → K nearest → ranking → results.

**Design requirements:**
- Hard filters (e.g. max price, location) applied **before** ML ranking (AGENTS §15).
- Feature set matches the DB schema (AGENTS §13) — no ML features that cannot be obtained from real DB records (AGENTS §41).
- Extensible: new features added without rewriting the engine (Spec §10).
- K configurable via settings/service; initial K=5; evaluated in Chapter 4 (Spec §13, AGENTS §16).
- No fabricated scores; recommendations are similarity-based (AGENTS §17, §39).

---

## L. Security Architecture

Controls (from AGENTS §19, `AGENTS.md` §44-45, Spec §28-30):

- Password hashing + Django auth + password validation.
- JWT authentication (SimpleJWT) with access/refresh.
- Role-based authorization on every protected endpoint.
- CSRF protection (Django middleware) + CSRF_TRUSTED_ORIGINS in production.
- Input validation server-side (never trust client).
- SQL injection protection via Django ORM (no raw SQL without justification).
- XSS protection (Django template auto-escaping).
- Secure session cookies; `DEBUG=False` in production; secure `SECRET_KEY` from env.
- Env variables for all secrets; `.env` never committed; provide `.env.example`.
- File-upload validation: file type, size, safe filenames, store outside executable paths, limit uploads.
- Auth throttling + API throttling where appropriate.
- Error handling: no stack traces/credentials/internal paths exposed to users; logs for technical errors (AGENTS §22).
- `ALLOWED_HOSTS` + HTTPS in production.
- Use `python manage.py check --deploy` for production verification (Spec §37).

---

## M. Testing Architecture

**Stack:** Django Test Framework + pytest + pytest-django (Spec §25).

**Strategy** (AGENTS §26-27, Spec §32-33):
- **Unit tests:** models, serializers, permissions, recommendation calculations, preprocessing, normalisation, weighting, distance, ranking, utilities.
- **Integration tests:** registration→login, landlord→apartment, tenant→preferences, preferences→recommendation, tenant↔landlord messaging, landlord→verification.
- **API tests:** GET/POST/PATCH/DELETE, auth, authorization, invalid & unauthorized requests.
- **ML tests (dedicated):** feature construction, normalisation, weight application, weighted-distance correctness, ascending ranking, missing/invalid handling, hard-filter behaviour, K behaviour, limited-candidate stability, and known-value numerical cases.
- **ML evaluation:** Precision@K, Recall@K, Hit Rate@K, NDCG@K + manual preference-test scenarios.
- **System tests:** functional correctness, security, usability, performance, API reliability, DB integrity, recommendation behaviour, cross-module integration.

Test directory layout: `tests/unit`, `tests/integration`, `tests/api`, `tests/ml` (Spec §20).

---

## N. Development Environment

- Windows 11 host; Python 3.13.x; VS Code; Git; PostgreSQL 18 local; Django.
- **Virtual environment:** `.venv` (mandatory — AGENTS §45; do not install project deps globally).
- `.env` for local secrets; `.env.example` committed without credentials.
- Local DB: `landlord_tenant_db`, user `postgres`, host `127.0.0.1:5432`.
- Tooling: VS Code (Python/Django extensions), Git CLI, GitHub remote.

---

## O. Production Deployment Architecture

**Primary target (per spec §37):** Render

```
INTERNET → HTTPS → (Nginx if self-host / Render edge) → Gunicorn → Django → PostgreSQL 18
```

- Django Web Service on Render; Gunicorn as WSGI.
- Managed PostgreSQL (Render).
- Static files via WhiteNoise (`collectstatic --noinput`).
- HTTPS enabled.
- Environment variables in Render dashboard.
- Migrations: `python manage.py migrate`; checks: `python manage.py check --deploy`.
- `DEBUG=False`, secure cookies, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` configured.

**Alternative (AGENTS §44):** Self-hosted Linux with Nginx reverse proxy + Gunicorn + PostgreSQL + HTTPS.

---

## P. Project Directory Structure

Per Spec §20 (with minor refinement consistent with AGENTS §7):

```
landlord_tenant_project/
├── .venv/
├── .env                      (never committed)
├── .env.example
├── .gitignore
├── README.md
├── AGENTS.md
├── requirements.txt
├── manage.py
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

---

## Q. Dependencies / Packages (Minimum Required)

**Runtime / development (from Spec §26):**

| Package | Purpose |
|---------|---------|
| `Django` | Web framework, ORM, auth, admin, templates |
| `djangorestframework` | REST API layer |
| `djangorestframework-simplejwt` | JWT authentication |
| `django-filter` | Search/filter for apartment APIs |
| `drf-spectacular` | OpenAPI/schema + Swagger docs |
| `psycopg[binary]` | PostgreSQL driver |
| `python-dotenv` | Load `.env` |
| `Pillow` | Image processing/validation |
| `numpy` | Numerical computation for KNN |
| `pandas` | Feature/data processing |
| `scikit-learn` | Preprocessing utilities + evaluation metrics |
| `gunicorn` | Production WSGI server |
| `whitenoise` | Production static serving |
| `pytest` | Test framework |
| `pytest-django` | Pytest integration with Django |

Versions pinned in `requirements.txt` **after** successful installation + testing (Spec §26). Do not add packages beyond these approved lists without approval.

---

## R. Requirement-to-Technology Traceability Matrix

| Requirement (Source) | Technology Used | Verified |
|----------------------|-----------------|----------|
| Python backend (AGENTS §4, Spec §25) | Python 3.13.x | Yes |
| Django framework (AGENTS §4, Spec §25) | Django 6.1 (verify) | Yes |
| REST API (AGENTS §4, Spec §21) | Django REST Framework | Yes |
| PostgreSQL (AGENTS §4, Spec §17) | PostgreSQL 18 (verify) + psycopg[binary] | Yes |
| JWT auth (Spec §22, §28) | djangorestframework-simplejwt | Yes |
| RBAC permissions (AGENTS §8, Spec §22) | Custom permission classes | Yes |
| Search/filter (Spec §6, §25) | django-filter | Yes |
| Weighted KNN (AGENTS §11-16, Spec §8-13) | NumPy/pandas/scikit-learn + custom `ml/weighted_knn.py` | Yes |
| Min-Max normalisation (Spec §12) | scikit-learn MinMaxScaler or custom | Yes |
| ML evaluation metrics (Spec §33) | scikit-learn metrics + custom evaluation.py | Yes |
| Bootstrap UI (Spec §25) | Bootstrap 5 | Yes |
| Image upload (Spec §29, §25) | Pillow | Yes |
| Env variables (AGENTS §20, Spec §27) | python-dotenv + `.env` | Yes |
| Static files (Spec §37) | WhiteNoise | Yes |
| API docs (Spec §25) | drf-spectacular | Yes |
| Testing (Spec §32, AGENTS §26-28) | Django Test Framework + pytest + pytest-django | Yes |
| Prod server (Spec §37, AGENTS §44) | Gunicorn + Nginx/Render + HTTPS | Yes |
| Version control (AGENTS §29, Spec §38) | Git + GitHub | Yes |

---

## S. Identified Conflicts and Resolutions

| # | Issue | Type | Recommended Resolution |
|---|-------|------|------------------------|
| 1 | **Django 6.1** and **PostgreSQL 18** are cutting-edge versions that may not exist or be fully stable / Django-Postgres compatible at setup time. | Ambiguity / risk | **Verify during Phase 1.** If the stated versions are unavailable, pin the nearest stable compatible versions (e.g. current stable Django LTS and current stable PostgreSQL) and document the substitution. No architecture change; purely version pinning. |
| 2 | **Python 3.13.x vs Django version compatibility.** | Consistency | Confirm Django version officially supports Python 3.13 before installing. Fall back to a supported Python if needed (documented). |
| 3 | **Templates vs SPA consumption of API.** Spec says both "Django can also serve the main web interface" and "frontend should communicate with the Django API where appropriate." | Minor ambiguity | Use server-rendered Django Templates for pages and fetch from the DRF API for interactive parts (search, recommendations, messages). No React. Document the split. |
| 4 | **Nginx in production** is in AGENTS.md §44 and Spec §36 diagram, but the **recommended primary deploy is Render** (Spec §37) which uses its own edge + WhiteNoise. | Technical inconsistency | Follow Spec §37 (Render + Gunicorn + WhiteNoise + managed Postgres) as primary. Treat Nginx as the documented alternative for self-hosted Linux deployment (AGENTS §44). No conflict with scope. |
| 5 | `scikit-learn` is listed in ML libs, but the Weighted KNN itself is custom and must not be replaced. | Potential misuse | Use scikit-learn **only** for preprocessing utilities and evaluation metrics (MinMaxScaler, metrics). The Weighted KNN *algorithm* remains custom in `ml/weighted_knn.py` per spec. Noted to preserve correctness. |
| 6 | Recommendation list endpoint `GET /api/v1/recommendations/` stores results in DB (`recommendations` table) — confirms a persistent `recommendations` entity. | Clarification | Store generated recommendation records (tenant, apartment, distance, rank, k, algorithm, timestamp) for history/reporting. |
| 7 | Messaging uses HTTP only in V1; WebSockets explicitly deferred. | Scope guard | Use standard DRF HTTP endpoints. Do not add channels/WebSockets unless testing proves real-time need (Spec §15). |

---

## T. Scope Protection / Out-of-Scope Features

**Do NOT add** (AGENTS §37-38, Spec §40, §39):

- Legal property-ownership determination or government land-document verification.
- Rent/payment processing or payment gateways.
- Signing tenancy agreements.
- Acting as / replacing a licensed estate agent; legal advice.
- Property maintenance management.
- Landlord-tenant dispute resolution.
- Guaranteeing apartment availability or truthful property information.
- Collaborative filtering / matrix factorisation / neural networks / deep learning / LLM recommenders / hybrid recommenders / external recommendation APIs.
- React SPA (unless explicitly requested).
- Microservices.
- Unnecessary Docker/Kubernetes infrastructure (unless explicitly approved).
- Cryptocurrency, blockchain, facial recognition, biometric auth, chatbots, social network, credit scoring, insurance.
- Self-approval of landlords.
- WebSockets/real-time messaging for V1.
- Any fabricated scores, fake verification statuses, or fabricated test results.

---

## U. Implementation Phases

Development proceeds incrementally (Agile). Each phase is implemented, tested, verified, reviewed against AGENTS.md, and committed before moving on (AGENTS §31).

**Consolidated order (from AGENTS §30 and Spec §41):**

1. **Phase 1 — Environment:** verify Python/Django/Postgres versions, create `.venv`, install approved deps, Git init, GitHub remote, `.env`/`.env.example`, config settings split.
2. **Phase 2 — Project Configuration:** `config/` settings (base/development/production), urls, asgi/wsgi, base template/static setup, DB connection to `landlord_tenant_db`.
3. **Phase 3 — Authentication & Roles:** custom User model, roles, registration, login/logout, JWT, permission classes, auth endpoints + tests.
4. **Phase 4 — Landlord & Apartment:** Landlord profile, Apartment model, ApartmentImage, CRUD, availability, validation, image-upload security, apartment endpoints + tests.
5. **Phase 5 — Tenant, Preferences, Search & Filtering:** Tenant profile, TenantPreference model, search/filtering with django-filter, preference endpoints + tests.
6. **Phase 6 — Landlord Verification:** verification model + submission/status + admin review (approve/reject) + tests.
7. **Phase 7 — Weighted KNN ML Component:** `ml/` modules (features, preprocessing, weighted_knn, ranking, evaluation) with dedicated ML tests (numerical known-value cases).
8. **Phase 8 — Recommendation API/UI:** generate/list/retrieve endpoints, persistent recommendation records, results UI ("Recommended for you"/"Preference match").
9. **Phase 9 — Messaging:** conversation/message models, endpoints, UI + tests.
10. **Phase 10 — Frontend & Dashboards:** public pages, tenant/landlord/admin dashboards, Bootstrap 5, admin management pages.
11. **Phase 11 — API Documentation:** drf-spectacular OpenAPI + Swagger.
12. **Phase 12 — Testing & ML Evaluation:** full unit/integration/API/system tests; Precision@K/Recall@K/HitRate@K/NDCG@K + manual preference scenarios.
13. **Phase 13 — Security Hardening:** throttling, upload validation, `check --deploy`, env secrets, CSRF/ALLOWED_HOSTS.
14. **Phase 14 — Production Deployment:** Gunicorn, WhiteNoise, managed PostgreSQL, HTTPS, migrations, `collectstatic`, deploy to Render.
15. **Phase 15 — Documentation:** README complete (description, stack, install, env, DB, migrations, commands, testing, ML explanation, deployment).

---

## Summary

### 1. Final Recommended Technology Stack (condensed)

- **Language:** Python 3.13.x
- **Web Framework:** Django 6.1 (verify availability)
- **API:** Django REST Framework
- **Auth:** djangorestframework-simplejwt (JWT) + role-based permissions
- **Database:** PostgreSQL 18 (verify) + psycopg[binary]
- **Filtering:** django-filter
- **ML:** NumPy, pandas, scikit-learn (preprocessing/metrics only) + **custom Weighted KNN** in `ml/`
- **Frontend:** HTML5/CSS3/JavaScript + Django Templates + Bootstrap 5 (no React)
- **Images:** Pillow
- **Env:** python-dotenv
- **Static:** WhiteNoise
- **API docs:** drf-spectacular
- **Server/Deploy:** Gunicorn + Render (managed PostgreSQL), HTTPS; Nginx documented as self-host alternative
- **Git:** Git + GitHub
- **Testing:** Django Test Framework + pytest + pytest-django

### 2. Issues Requiring Approval Before Implementation

1. **Version verification:** Django 6.1 and PostgreSQL 18 (and Python 3.13 × Django compatibility) must be confirmed at environment setup. If unavailable/unsupported, I will pin the nearest stable compatible versions and document the substitution. **This is the main approval point.**
2. **Recommendation result persistence:** I will store generated recommendations in a `recommendations` table (per spec §14/§17) — confirms the persistent entity interpretation.
3. **scikit-learn usage boundary:** It will be used only for preprocessing/metrics, never to replace custom Weighted KNN — confirming this aligns with your intent.

### 3. Confirmation

**NO application code was written, modified, or deleted during this analysis. No packages were installed, no database tables created, and no migrations generated.** This was an analysis-only task producing `TECH_STACK_AND_IMPLEMENTATION_PLAN.md`.
