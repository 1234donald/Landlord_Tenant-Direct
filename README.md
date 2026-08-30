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
- **Sprint 2.5 (completed):** Permissions and role-based access — four reusable
  permission classes in `apps/accounts/permissions.py`: `IsTenant`, `IsLandlord`,
  `IsAdmin` and `IsOwnerOrAdmin`. Protected role-scoped endpoints under
  `/api/v1/accounts/` enforce RBAC: `tenant/` (IsTenant), `landlord/`
  (IsLandlord), `users/` admin-only user list (IsAdmin), and `users/{pk}/`
  (IsOwnerOrAdmin — a user may view only their own profile or an admin any).
  Phase exit criteria verified: tenants cannot access landlord/admin functions,
  landlords cannot access admin functions, administrator routes protected.
  13 permission API tests (64 total). **Phase 2 (authentication & user
  management) is complete.**
- **Sprint 3.1 (completed):** Landlord verification data model — the
  `VerificationRequest` model in `apps/verification/models.py` supporting the
  administrative landlord-verification workflow. Fields: `landlord` (required
  FK to a LANDLORD user), `information`, `status` (PENDING/APPROVED/REJECTED,
  default PENDING), `remarks`, `submitted_at` (auto), `reviewed_by` (optional FK
  to the reviewing ADMIN, SET_NULL on deletion), `reviewed_at`, `updated_at`.
  Registered in Django Admin; migration `verification.0001_initial` applied.
   It is an administrative platform control only and makes no legal
   property-ownership claims. 15 model tests (79 total).
- **Sprint 3.2 (completed):** Landlord verification workflow — the Verification
  API (§24.6) implemented in `apps/verification/`:
  `POST /api/v1/verification/submit/` (landlord submission, blocks a duplicate
  while a request is PENDING, validates non-blank information within 5000 chars),
  `GET /api/v1/verification/status/` (landlord views own requests), and the
  admin review endpoints `GET /api/v1/admin/verifications/` (list + validated
  `?status=` filter), `POST /api/v1/admin/verifications/{id}/approve/` and
  `.../{id}/reject/` (only PENDING requests can be reviewed; remarks validated
  for rejections). Role-based access enforced via `IsLandlord`/`IsAdmin`.
  `VerificationRequest.approve(admin)` / `.reject(admin, remarks)` domain methods
  implement the state transitions. 19 verification API tests (98 total).
- **Sprint 3.3 (completed):** Apartment data model — the `Apartment` model in
  `apps/apartments/models.py` representing landlord apartment listings with:
  `landlord` (required FK to a LANDLORD user), `title`, `description`, `location`,
  `address`, `rental_price` (positive decimal), `apartment_type`
  (Self-contained / One / Two / Three-bedroom / Flat / Duplex), `bedrooms` and
  `bathrooms` (positive counts), facility flags (`parking`, `electricity`, `water`,
  `security`, `furnished`) plus a free-text `additional_facilities` field, and an
  `availability` flag, with `created_at`/`updated_at` timestamps. Validation
  (via `clean()`) enforces a positive rental price and valid bedroom/bathroom
  counts. Indexes cover `location`, `rental_price`, `apartment_type`, `landlord`
   and `availability` for search/filtering. Registered in Django Admin; migration
   `apartments.0001_initial` applied. 16 model tests (114 total).
- **Sprint 3.4 (completed):** Apartment creation and media — the landlord-only
  `POST /api/v1/apartments/` endpoint creates a listing owned by the
  authenticated landlord (ownership is never client-supplied) and accepts
  multimedia image uploads. Includes the `ApartmentImage` model
  (`apartment` FK, `image` ImageField, `order`, `uploaded_at`; migration
  `apartments.0002_apartmentimage` applied) and validated image uploads for
  file type/extension, a 5 MB size limit, and real image-content verification
  via Pillow (rejects arbitrary/non-image payloads disguised as images).
  Listing validation (positive price, ≥1 bedrooms/bathrooms, valid type) is
  enforced in `apps/apartments/serializers.py`. Invalid uploads never leave a
   partial listing behind. Registered in Django Admin; 14 apartment creation
   API tests (128 total).
- **Sprint 3.5 (completed):** Apartment update, delete and availability —
   `PATCH /api/v1/apartments/{id}/` edits a listing (or a subset of its fields
   via partial update), flips its `availability` status, and optionally replaces
   the full image set when new files are supplied; `DELETE /api/v1/apartments/{id}/`
   removes a listing (cascading its media). Access is enforced by the
   `IsApartmentOwnerOrAdmin` permission class so only the owning landlord or an
   administrator may modify or delete a listing; a tenant or a different
   landlord is rejected. Image replacement reuses the same validation pipeline
   as creation, and new files must all pass before old media is removed so a
   failed update never leaves a listing without images. No database changes were
   required; 19 apartment-management API tests (147 total).
- **Sprint 3.6 (completed):** Apartment presentation and module testing — a
   read-oriented HTML presentation layer (`apps/apartments/presentation.py` +
   `templates/apartments/`) built on Django generic views and the existing
   Bootstrap base template. `/apartments/` renders available apartments as cards
   (cover image, location, price, type, beds/baths, availability badge);
   `/apartments/{id}/` renders full listing details with a media gallery,
   facilities display, furnishing and availability status, and the landlord's
   permitted information (name and email); `/my/apartments/` is a landlord-only
   page listing a landlord's own apartments (admins may view all, tenants are
   forbidden). The browse page filters out unavailable listings. 19 module tests
   (166 total); no database changes were required.
- **Sprint 4.1 (completed):** Apartment search — a public
   `GET /api/v1/apartments/` endpoint (added to `ApartmentListCreateView`) that
   performs basic search by location (case-insensitive), apartment type (exact,
   validated against the allowed types), rental price (optional `min_price` /
   `max_price`) and bedroom/bathroom count, with the ability to combine any of
   these criteria. Invalid parameter values return a 400 with field-specific
   errors rather than silently returning misleading results, and the response
   uses the standard list envelope. The presentation browse page
   (   `/apartments/`) gained a matching search form wired to the same filters.
   18 search tests (184 total); no database changes were required.
- **Sprint 4.2 (completed):** Combined filtering and pagination — the
   `GET /api/v1/apartments/` endpoint now supports combined filtering across all
   listing attributes: price range (`min_price` / `max_price`), location,
   apartment type, bedrooms, bathrooms, facility flags (`parking`,
   `electricity`, `water`, `security`, `furnished`) and availability. Facility
   and availability booleans accept `true/false`, `1/0`, `yes/no` and `on/off`,
   with invalid values rejected by a 400 (never silently ignored). The response
   is paginated (page size 12) and includes `count`, `page`, `pages`, `next`
   and `previous` metadata while preserving the other filters in the page links.
   The presentation browse page (`/apartments/`) gained matching facility
   checkboxes in its search form. 14 filter/pagination tests (198 total); no
   database changes were required.
- **Sprint 4.3 (completed):** Tenant preference data model — the
   `Preference` model (`apps/recommendations/models.py`) persists a tenant's
   apartment preferences and forms the future Weighted KNN query vector
   ``U``. Each preference belongs to a TENANT user
   (`tenant` FK, `related_name="preferences"`, mirroring the
   `Apartment.landlord` relationship) and stores the preferred `location`,
   `max_rent` (maximum rental price), `apartment_type` (same choices as
   `Apartment`), `bedrooms`, `bathrooms`, facility preferences (`parking`,
   `electricity`, `water`, `security`, `furnished`) and `additional_facilities`.
   Facility preferences are nullable booleans so a tenant can express required /
   not-required / no-preference. Model validation enforces a positive
   `max_rent` and bedroom/bathroom counts of at least 1, matching the
   `Apartment` validation. The model is registered in Django admin and
   migrated to PostgreSQL. 15 model tests (213 total).
- **Sprint 4.4 (completed):** Tenant preference management — the
   Preference API implemented in `apps/recommendations/`:
   `GET/POST /api/v1/preferences/` (list / create, TENANT role) and
   `GET/PATCH/DELETE /api/v1/preferences/{id}/`
   (retrieve / update / delete, owner-or-admin via
   `IsPreferenceOwnerOrAdmin`). Ownership is always the authenticated
   tenant and is never client-supplied. A service layer
   (`apps/recommendations/services.py`) keeps business logic out of views
   and prepares the stored preference as recommendation-ready query data
   (the future Weighted KNN vector `U`), without performing any similarity
   calculation. 31 preference tests (244 total); no database changes.
- **Sprint 4.5 (completed):** Messaging and conversations — the
   tenant–landlord messaging module in `apps/messaging/`:
   `Conversation` and `Message` models (a conversation links one TENANT and
   one LANDLORD with a unique pair, and a message records sender, recipient,
   body, `SENT`/`READ` status and timestamps; migration
   `messaging.0001_initial` applied). The API (§24.5):
   `GET/POST /api/v1/messages/` (list own / send, creating or reusing the
   tenant-landlord conversation), `GET /api/v1/messages/{id}/`,
   `GET/POST /api/v1/conversations/` (list own / create),
   `GET /api/v1/conversations/{id}/` (history) and
   `POST /api/v1/conversations/{id}/messages/` (reply). Access is private
   to the two participants or an administrator; retrieving a conversation
   marks the recipient's incoming messages as `READ`. A landlord or another
   tenant can never read or send in a conversation they do not belong to.
   Registered in Django admin. 45 messaging tests (289 total).
- **Sprint 4.6 (completed):** Tenant journey integration — end-to-end
   tenant-flow integration tests in `tests/integration/test_tenant_journey.py`
   chain the Phase 4 modules into one working journey
   (`Tenant → Search → Filter → View Apartment → Save Preferences →
   Contact Landlord → Messages`). Each test drives the real HTTP API and
   presentation pages: a tenant registers and logs in, a landlord creates
   listings, the tenant searches and filters, views apartment details, saves
   preferences, contacts the landlord, and reads/replies within the
   conversation. This verifies that authentication, apartment search/filter/
   details, tenant preferences and messaging interoperate correctly and that
   the Sprint 4.6 phase exit criteria are satisfied. No new UI was built here
   (frontend dashboards are later-phase work). 4 integration tests (293 total
   across the suite at this point); no database changes were required.
- **Sprint 5.1 (completed):** Weighted KNN feature specification — the
   confirmed recommendation feature set for the recommendation component,
   specified in `ml/feature_specification.md` and mirrored by the
   authoritative constants in `ml/features.py`. It fixes the nine distance
   features (`rental_price`, `bedrooms`, `bathrooms`, `apartment_type`, and
   the facility binaries `parking`/`electricity`/`water`/`security`/
   `furnished`), classifies them as numerical / categorical / binary, maps
   each to its `Apartment` and `Preference` database fields, defines the
   configurable non-negative feature weights (defaults with `rental_price`
   weighted highest), and defines the hard filters applied before similarity
   ranking (availability, location, price cap, apartment type, unit minimums
   and required facilities — consistent with the existing search/filter
   logic). `DEFAULT_K=5` is set as the configurable neighbour count. 21
   feature-specification tests (314 total); no database changes.
- **Sprint 5.2 (completed):** Feature extraction and encoding — the
   feature-processing pipeline implementated in `ml/preprocessing.py`.
   It builds the apartment candidate vector `A` (`apartment_feature_vector` /
   `encode_apartment_vector`) and the tenant query vector `U`
   (`preference_feature_vector` / `encode_tenant_vector`), one-hot encodes the
   categorical `apartment_type` into its six columns
   (`one_hot_encode_apartment_type`), encodes binary facilities as 0/1
   (`encode_binary`), and handles missing (unstated) tenant preferences:
   nullable values are preserved as `None` and reported through an `active`
   mask so unstated dimensions can be neutralised at weighting time
   (`validate_encoded_pair` guards vector shape consistency). Numerical values
   are emitted as raw floats (min-max normalisation is Sprint 5.3). All
   encoding draws on the Sprint 5.1 feature constants. 13 preprocessing tests
   (327 total); no database changes.
- **Sprint 5.3 (completed):** Numerical normalisation — the tested
   normalisation service in `ml/preprocessing.py`. It min-max normalises the
   numerical features (`rental_price`, `bedrooms`, `bathrooms`) using
   `x' = (x − xmin)/(xmax − xmin)`, protects against division by zero when a
   feature is constant across the candidate set (returns `0.0` instead of
   dividing), and provides `feature_bounds`/`min_max_normalise`/
   `normalise_apartments`/`normalise_tenant_vector`. Bounds are computed across
   the eligible candidate apartments so every candidate `A` and the tenant query
   vector `U` share a common normalisation frame; categorical one-hot and binary
   dimensions pass through unchanged and missing (`None`) tenant values are
   preserved. 15 normalisation tests (342 total), including known-value cases;
   no database changes.
- **Sprint 5.4 (completed):** Feature weighting and weighted distance — the
   weighted-distance engine in `ml/weighted_knn.py`. It resolves the effective
   feature weights (`resolve_weights`: Sprint 5.1 defaults or a validated
   override) and computes the weighted Euclidean distance
   `Dw(U,A) = sqrt(Σ wi·(ui − ai)²)`. The categorical `apartment_type` maps
   back to its base weight when a type is stated; unstated (missing)
   preferences are neutralised at weighting time via the Sprint 5.2 `active`
   mask (or a `None` value), so out-of-scope dimensions never inflate the
   distance. A bounded `similarity` helper (exponential decay of the distance)
   provides an interpretive "preference match" score for display. 18
   weighted-distance tests (360 total), including known-value mathematical
   cases (identity → 0, single-dimension weights, custom weights, type match
   vs mismatch); no database changes.
- **Sprint 5.5 (completed):** KNN candidate selection and ranking — the
   Weighted KNN ranking engine in `ml/ranking.py`. Once a tenant's stored
   `Preference` is available, the engine retrieves the eligible apartments
   (`hard_filter_queryset`), applies the Sprint 5.1 hard filters before any
   similarity ranking (availability, location, price cap, exact apartment
   type, bedroom/bathroom minimums and required facilities), composes the
   Phase 5 encoding/normalisation/distance components to score every eligible
   candidate, sorts by ascending distance (smallest = most relevant, AGENTS
   12), selects the K nearest (configurable `DEFAULT_K`), and assigns 1-based
   ranking positions. When fewer than K candidates are eligible, all of them
   are returned (still ranked). The primary entry point is
    `recommend(queryset, preference, k, weights)`. 15 ranking tests (375 total),
    including the price-cap exclusion, ascending order, K selection and
    limited-candidate cases; no database changes.
- **Sprint 5.6 (completed):** Django/API/UI recommendation integration — the
    full preference-to-recommendation flow is now live. Two persistence models
    were added: `Recommendation` (tenant, preference, algorithm, configurable
    `k`, created-at) and `RecommendationItem` (apartment, rank, distance,
    similarity), giving the required `Tenant ── Recommendation ── Apartment`
    relationship (SYSTEM_REQUIREMENTS §25–26). The service function
    `generate_recommendations` (`apps/recommendations/services.py`) drives the
    `ml` engine and persists each run, raising `NoPreferenceError` when a
    tenant has (or owns) no preference. New API endpoints (§24.4):
    `POST /api/v1/recommendations/generate/` (uses the latest preference or an
    optional `preference_id`), `GET /api/v1/recommendations/` (tenant's runs),
    and `GET /api/v1/recommendations/{id}/` (owning tenant or admin). A
    tenant-facing results page (`templates/recommendations/results.html`)
    renders ranked apartment cards with "Recommended for you" and "Similarity
    score" wording (AGENTS 43) and a regenerate form. 6 service tests, 15 API
    tests and 3 page tests were added (399 total); migration `0002` creates the
    new tables.
- **Sprint 5.7 (completed):** recommendation validation and evaluation
    readiness — the evaluation deliverable `ml/evaluation.py` implements the
    four §31 metrics (Precision@K, Recall@K, Hit Rate@K, NDCG@K) as pure
    Python functions over ranking results vs a ground-truth relevance set, plus
    an `evaluate()` helper returning all four. `ml/evaluation_scenarios.py`
    supplies deterministic, clearly-labelled test/evaluation data (AGENTS 40).
    Validation runs the real Weighted KNN engine against a controlled apartment
    catalogue seeded as actual `Apartment` records and verifies the Phase 5 exit
    criteria: real records are ranked (not placeholders), scores are real
    (similarity ≡ exp(-distance)), lower distance → higher rank, results are
    reproducible, hard filters / K / missing-data behave correctly, and
    evaluation metrics are computed from actual ranking output. 19 metric tests
    + 8 validation tests were added in the new `tests/ml/` directory (426
    total); no database changes.

Sprint 5.7 completes Phase 5's validation and evaluation-readiness work: the
Weighted KNN component is reproducible, its exit criteria are verified against
real apartment records, and the evaluation metrics required for Chapter Four
(Precision@K, Recall@K, Hit Rate@K, NDCG@K) are implemented and unit-tested.
This closes out the Weighted KNN recommendation phase; Phase 6 (administration,
security and system integration) follows, with frontend dashboards later.

Sprint 5.4 completes the recommendation weighted-distance engine. A tenant
query vector and each apartment candidate can now be compared by a weighted
similarity score that honours stated preferences and configuration. Candidate
selection, hard filtering, K-selection and ascending ranking (Sprint 5.5),
evaluation and the recommendation API/UI remain in this phase; frontend
dashboards and administration are later phases.
