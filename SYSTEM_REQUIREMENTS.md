# SYSTEM REQUIREMENTS AND ARCHITECTURE SPECIFICATION

## Project Title
**Design and Implementation of an Online Platform for Direct Landlord-to-Tenant Contact Using Artificial Intelligence and Machine Learning Techniques**

## System Name
**Landlord–Tenant Direct Connect Platform**

## Document Purpose
This document defines the functional requirements, non-functional requirements, system architecture, technology stack, database structure, API structure, security requirements, machine-learning recommendation requirements, development workflow, build phases, sprint plan, testing strategy, and deployment configuration for the proposed platform.

This document must be used together with `AGENTS.md`. Where implementation decisions are unclear, `AGENTS.md` and this system requirements document must be treated as the authoritative project constraints.

---

# 1. PROJECT OVERVIEW

The proposed system is a web-based platform designed to facilitate direct interaction between landlords and prospective tenants.

The platform shall allow:

- prospective tenants to register and search for apartments;
- landlords to register and manage residential apartment listings;
- tenants to provide apartment preferences;
- the system to generate personalised apartment recommendations using Weighted K-Nearest Neighbour (Weighted KNN);
- tenants and landlords to communicate directly;
- administrators to manage users, listings and landlord verification activities.

The system is an academic prototype and shall not be represented as a legal property-ownership verification platform, payment platform, tenancy-contract system, or full commercial real-estate marketplace.

---

# 2. DEVELOPMENT METHODOLOGY

The project shall follow:

- **Agile Software Development Methodology** as the overall development methodology;
- **Object-Oriented Analysis and Design (OOAD)** as the analysis and system-design approach;
- **Django/Python** as the primary application-development platform;
- **PostgreSQL** as the relational database;
- **Weighted KNN** as the machine-learning recommendation algorithm;
- **Testing and Evaluation** as the validation stage.

The project-development relationship is:

```text
Agile
  ↓
Requirements Analysis
  ↓
OOAD
  ↓
Logical and Physical Design
  ↓
Django/Python Implementation
  ↓
PostgreSQL
  ↓
Weighted KNN
  ↓
Integration
  ↓
Testing and Evaluation
  ↓
Deployment
```

---

# 3. PRIMARY USER ROLES

The system shall support three principal user roles:

1. **Tenant**
2. **Landlord**
3. **Administrator**

Administrator accounts shall not be available through unrestricted public registration.

---

# 4. FUNCTIONAL REQUIREMENTS

## FR-001 User Registration

The system shall allow prospective tenants and landlords to register.

Required registration data shall include:

- full name;
- email;
- phone/contact information;
- password;
- user role.

The system shall prevent duplicate email accounts.

---

## FR-002 User Authentication

The system shall provide:

- login;
- logout;
- password hashing;
- secure authentication;
- password reset where implemented;
- session/token management;
- role-based authorization.

The API authentication mechanism shall use JWT where REST API authentication is required.

---

## FR-003 Tenant Profile Management

A tenant shall be able to:

- view profile;
- edit profile;
- maintain contact information;
- manage apartment preferences.

---

## FR-004 Landlord Profile Management

A landlord shall be able to:

- view profile;
- edit profile;
- submit verification information;
- view verification status;
- manage apartment listings.

---

## FR-005 Administrator Management

An administrator shall be able to:

- manage users;
- review landlords;
- review verification submissions;
- approve or reject landlord verification;
- manage apartment listings;
- remove inappropriate listings where required;
- monitor relevant system activity;
- access administrative reports.

---

# 5. APARTMENT MANAGEMENT REQUIREMENTS

Each apartment record shall contain, where applicable:

- apartment ID;
- landlord;
- title;
- description;
- location;
- address/area;
- rental price;
- apartment type;
- number of bedrooms;
- number of bathrooms;
- parking availability;
- electricity availability;
- water availability;
- security availability;
- furnished/unfurnished status;
- additional facilities;
- availability status;
- apartment images;
- date created;
- date updated.

Supported apartment types may include:

- Self-contained;
- One-bedroom;
- Two-bedroom;
- Three-bedroom;
- Flat;
- Duplex.

The implementation shall allow apartment types to be extended later.

---

# 6. SEARCH AND FILTERING REQUIREMENTS

Tenants shall be able to search and filter apartments using:

- location;
- minimum price;
- maximum price;
- apartment type;
- bedrooms;
- bathrooms;
- facilities;
- availability.

Search filters shall remain separate from the machine-learning recommendation ranking.

Mandatory search constraints may be applied before Weighted KNN similarity calculation.

---

# 7. TENANT PREFERENCE REQUIREMENTS

The tenant-preference system shall support:

- preferred location;
- maximum rental price;
- preferred apartment type;
- preferred bedrooms;
- preferred bathrooms;
- parking preference;
- electricity preference;
- water preference;
- security preference;
- furnished/unfurnished preference;
- other supported facilities.

Preferences shall be stored in the relational database.

---

# 8. MACHINE-LEARNING RECOMMENDATION REQUIREMENTS

The principal intelligent component shall use:

**Weighted K-Nearest Neighbour (Weighted KNN)**

The implementation shall not replace the approved Weighted KNN recommendation approach with:

- collaborative filtering;
- matrix factorisation;
- deep learning;
- neural networks;
- external recommendation APIs;
- hybrid recommendation systems.

---

# 9. WEIGHTED KNN RECOMMENDATION PIPELINE

The recommendation pipeline shall be:

```text
Tenant Preferences
       ↓
Validation
       ↓
Mandatory / Hard Filtering
       ↓
Candidate Apartments
       ↓
Feature Extraction
       ↓
Categorical Encoding
       ↓
Numerical Normalisation
       ↓
Feature Weighting
       ↓
Weighted Distance Calculation
       ↓
K Nearest Candidates
       ↓
Ranking
       ↓
Recommendation Results
```

---

# 10. RECOMMENDATION FEATURE SET

The initial recommendation engine shall support features including:

- rental price;
- location;
- apartment type;
- bedrooms;
- bathrooms;
- parking;
- electricity;
- water;
- security;
- furnished status;
- additional supported facilities.

The recommendation architecture shall permit future features to be added without redesigning the entire system.

---

# 11. WEIGHTED DISTANCE MODEL

Let the tenant preference vector be:

```text
U = (u1, u2, ..., un)
```

and an apartment feature vector be:

```text
A = (a1, a2, ..., an)
```

The weighted Euclidean distance shall be:

```text
Dw(U,A) = sqrt(Σ wi(ui - ai)^2)
```

Where:

- `Dw(U,A)` = weighted distance between tenant and apartment;
- `wi` = weight assigned to feature i;
- `ui` = tenant-preference value;
- `ai` = apartment feature value;
- `n` = number of features.

Recommendation rule:

```text
Smaller Distance
      ↓
Greater Similarity
      ↓
Higher Recommendation Rank
```

---

# 12. FEATURE NORMALISATION

Numerical features shall be normalised where required.

The initial normalisation method shall be min-max normalisation:

```text
x' = (x - xmin) / (xmax - xmin)
```

The implementation shall safely handle cases where:

```text
xmax = xmin
```

to prevent division-by-zero errors.

---

# 13. CATEGORICAL FEATURE ENCODING

Categorical and binary attributes shall be converted to suitable machine-readable values.

Binary attributes may include:

- parking;
- electricity;
- water;
- security;
- furnished status.

Nominal categorical attributes such as apartment type shall not be encoded in a way that falsely introduces an ordinal relationship unless such a relationship is explicitly intended.

One-hot encoding or another suitable encoding approach may therefore be used.

---

# 14. FEATURE WEIGHTING

The recommendation engine shall support configurable feature weights.

Feature weights shall determine the contribution of each feature to the weighted-distance calculation.

Weights must not be inserted as unexplained arbitrary constants.

The final selected weights shall be documented and evaluated during system testing.

---

# 15. K VALUE REQUIREMENT

The recommendation engine shall support a configurable K value.

Initial development may use:

```text
K = 5
```

but the implementation shall allow K to be modified during evaluation.

The selected K shall be documented during Chapter Four testing and evaluation.

---

# 16. HARD FILTERS AND RECOMMENDATION RANKING

The system shall distinguish between:

1. mandatory constraints; and
2. recommendation similarity.

Example:

If a tenant specifies:

```text
maximum_price = 500000
```

an apartment above that amount may be excluded before Weighted KNN ranking.

The ML component shall rank eligible candidate apartments rather than override mandatory constraints.

---

# 17. MESSAGING REQUIREMENTS

The system shall allow direct communication between tenants and landlords.

Messaging functionality shall include:

- send message;
- receive message;
- conversation history;
- timestamps;
- message status where applicable.

Version 1 shall use conventional HTTP-based messaging.

Real-time WebSocket infrastructure is not required unless explicitly approved.

---

# 18. LANDLORD VERIFICATION REQUIREMENTS

The landlord-verification workflow shall be:

```text
Landlord Registration
        ↓
Information Submission
        ↓
Pending Verification
        ↓
Administrator Review
        ↓
Approve / Reject
        ↓
Verification Status Updated
```

Verification is an administrative system control.

The platform shall not claim to:

- legally verify property ownership;
- verify land title;
- verify government property documents;
- determine criminal status;
- make legal decisions.

---

# 19. SYSTEM MODULES

The system shall contain the following principal modules:

- Accounts/User Management;
- Tenant Management;
- Landlord Management;
- Apartment Management;
- Search and Filtering;
- Tenant Preferences;
- Recommendations;
- Messaging;
- Verification;
- Administration;
- System Monitoring/Logging.

---

# 20. BACKEND TECHNOLOGY STACK

The approved backend technology stack is:

| Component | Technology |
|---|---|
| Programming Language | Python 3.13.x |
| Web Framework | Django 6.x compatible release |
| REST API | Django REST Framework |
| ORM | Django ORM |
| Authentication | Django Authentication + JWT where API authentication is used |
| Filtering | django-filter |
| Database | PostgreSQL 18 |
| ML | Weighted KNN |
| Data Processing | NumPy / pandas / scikit-learn |
| Image Processing | Pillow |
| API Documentation | drf-spectacular / OpenAPI |
| Environment Management | `.env` / environment variables |
| Testing | Django test framework / pytest / pytest-django |

---

# 21. FRONTEND TECHNOLOGY STACK

The frontend shall use:

- HTML5;
- CSS3;
- JavaScript;
- Django Templates;
- Bootstrap 5 where useful.

React, Vue, Angular, Next.js or similar frontend frameworks shall not be added unless explicitly approved.

---

# 22. DEVELOPMENT TOOLING

Development tools shall include:

- Windows 11 development environment;
- Python virtual environment;
- Visual Studio Code;
- OpenCode CLI;
- Git;
- GitHub;
- PostgreSQL;
- pgAdmin;
- modern web browser.

---

# 23. DJANGO PROJECT STRUCTURE

The recommended project structure is:

```text
landlord_tenant_project/
│
├── manage.py
├── .env
├── .env.example
├── .gitignore
├── AGENTS.md
├── SYSTEM_REQUIREMENTS.md
├── README.md
├── requirements.txt
│
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── apartments/
│   ├── recommendations/
│   ├── messaging/
│   ├── verification/
│   └── core/
│
├── ml/
│   ├── features.py
│   ├── preprocessing.py
│   ├── weighted_knn.py
│   ├── ranking.py
│   └── evaluation.py
│
├── api/
│   └── v1/
│
├── templates/
├── static/
├── staticfiles/
├── media/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── api/
    └── ml/
```

Functional separation must be maintained even where the final directory structure is adjusted slightly during implementation.

---

# 24. API ARCHITECTURE

API base path:

```text
/api/v1/
```

## 24.1 Authentication API

```http
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/refresh/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
PATCH  /api/v1/auth/me/
```

---

## 24.2 Apartment API

```http
GET    /api/v1/apartments/
POST   /api/v1/apartments/
GET    /api/v1/apartments/{id}/
PATCH  /api/v1/apartments/{id}/
DELETE /api/v1/apartments/{id}/
```

Filtering examples:

```text
/api/v1/apartments/?location=Calabar
/api/v1/apartments/?max_price=500000
/api/v1/apartments/?bedrooms=2
```

---

## 24.3 Preference API

```http
GET    /api/v1/preferences/
POST   /api/v1/preferences/
GET    /api/v1/preferences/{id}/
PATCH  /api/v1/preferences/{id}/
DELETE /api/v1/preferences/{id}/
```

---

## 24.4 Recommendation API

```http
POST /api/v1/recommendations/generate/
GET  /api/v1/recommendations/
GET  /api/v1/recommendations/{id}/
```

Example recommendation response:

```json
{
  "algorithm": "weighted_knn",
  "k": 5,
  "results": [
    {
      "apartment_id": 12,
      "distance": 0.142,
      "rank": 1
    }
  ]
}
```

---

## 24.5 Messaging API

```http
GET  /api/v1/messages/
POST /api/v1/messages/
GET  /api/v1/messages/{id}/

GET  /api/v1/conversations/
GET  /api/v1/conversations/{id}/
POST /api/v1/conversations/{id}/messages/
```

---

## 24.6 Verification API

```http
POST /api/v1/verification/submit/
GET  /api/v1/verification/status/

GET  /api/v1/admin/verifications/
POST /api/v1/admin/verifications/{id}/approve/
POST /api/v1/admin/verifications/{id}/reject/
```

---

# 25. DATABASE ARCHITECTURE

Database:

```text
PostgreSQL 18
```

Development database:

```text
landlord_tenant_db
```

Primary entities:

- User (single custom model carrying the role field TENANT / LANDLORD / ADMIN
  and the profile fields full_name and phone; there is no separate "Tenant
  Profile" or "Landlord Profile" table — each role's profile is represented by
  the User record itself via the role field, and exposed through a
  ProfileSerializer);
- Apartment;
- Apartment Image;
- Tenant Preference;
- Recommendation;
- Conversation;
- Message;
- Verification.

---

# 26. DATABASE RELATIONSHIPS

A single custom `User` model represents every principal; its `role` field
distinguishes TENANT, LANDLORD and ADMIN. "Tenant" and "Landlord" are therefore
roles on the `User` entity rather than separate tables, and the preference /
listing relationships point at `User` (filtered by role):

```text
User (role = TENANT | LANDLORD | ADMIN)
 │
 ├── [as Tenant] ─── Tenant Preference     (Preference.tenant  FK → User)
 │
 └── [as Landlord] ─── Apartment           (Apartment.landlord FK → User)
                          │
                          └── Apartment Image


User[Tenant] ─── Recommendation ─── Apartment

User ─── Conversation/Message ─── User

User[Landlord] ─── Verification ─── User[Administrator]
```

Foreign-key relationships and referential integrity shall be enforced through Django models and PostgreSQL.

---

# 27. SECURITY REQUIREMENTS

The system shall implement:

- password hashing;
- authentication;
- role-based authorization;
- CSRF protection;
- XSS mitigation;
- server-side input validation;
- Django ORM protection against common SQL-injection patterns;
- secure cookies in production;
- secure environment variables;
- HTTPS in production;
- file-upload validation;
- protected administrative functionality;
- appropriate API permissions;
- request throttling where appropriate;
- secure error handling.

The system shall never hard-code:

- SECRET_KEY;
- production database passwords;
- API credentials;
- email credentials;
- production secrets.

---

# 28. ENVIRONMENT VARIABLES

Development configuration shall use environment variables such as:

```env
DEBUG=True
SECRET_KEY=

DATABASE_NAME=landlord_tenant_db
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432

ALLOWED_HOSTS=127.0.0.1,localhost
```

Production shall use:

```env
DEBUG=False
SECRET_KEY=

DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=
DATABASE_PORT=5432

ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
```

`.env` shall never be committed to Git.

`.env.example` shall be committed without real credentials.

---

# 29. NON-FUNCTIONAL REQUIREMENTS

## 29.1 Performance

Normal application/API requests should target response times below approximately two seconds under normal prototype load.

Recommendation response time shall be separately measured during evaluation.

## 29.2 Security

Users shall access only functions permitted by their assigned role.

## 29.3 Usability

The user interface shall be responsive, consistent and easy to navigate.

## 29.4 Reliability

The system shall validate data and handle predictable errors gracefully.

## 29.5 Maintainability

The application shall follow modular Django design and separation of concerns.

## 29.6 Scalability

The architecture shall permit an increase in:

- users;
- landlords;
- tenants;
- apartments;
- recommendations;
- messages.

The prototype is not required to demonstrate enterprise-scale traffic.

## 29.7 Compatibility

The application shall work through modern desktop and mobile web browsers.

---

# 30. TESTING REQUIREMENTS

The project shall include:

- unit testing;
- integration testing;
- API testing;
- system testing;
- access-control testing;
- ML testing;
- user-acceptance testing.

Tests shall not be reported as passed unless they have actually been executed successfully.

---

# 31. ML EVALUATION REQUIREMENTS

The recommendation component shall be evaluated for:

- feature construction correctness;
- normalisation correctness;
- weight application;
- weighted-distance correctness;
- ranking correctness;
- K-value behaviour;
- hard-filter behaviour;
- response time;
- recommendation relevance;
- stability under different tenant preferences.

Where appropriate and supported by the evaluation dataset, recommendation metrics may include:

- Precision@K;
- Recall@K;
- Hit Rate@K;
- NDCG@K.

No recommendation-performance metric shall be fabricated.

---

# 32. PRODUCTION ARCHITECTURE

The recommended production architecture is:

```text
Internet
   │
 HTTPS
   │
   ▼
Reverse Proxy / Hosting Edge
   │
   ▼
Gunicorn
   │
   ▼
Django Application
   │
   ├── REST API
   ├── Business Logic
   ├── Authentication
   └── Weighted KNN
   │
   ▼
PostgreSQL
```

Production deployment may use Render or an equivalent approved host.

Static files may be served using WhiteNoise or the deployment platform's recommended static-file configuration.

Nginx may be used where deployment is performed on a self-managed Linux server.

---

# 33. PROJECT SCOPE RESTRICTIONS

The system shall not:

- process rent payments;
- determine legal property ownership;
- validate land titles;
- sign tenancy agreements;
- provide legal advice;
- act as a legal property authority;
- perform criminal background checks;
- provide biometric identification;
- use blockchain;
- implement cryptocurrency;
- implement facial recognition;
- implement unnecessary deep-learning models;
- introduce unrelated commercial features.

---

# 34. BUILD PHASES AND AGILE SPRINT PLAN

Development shall be organised into seven controlled build phases.

Each phase shall contain **between five and seven sprints**, depending on the magnitude and complexity of the phase.

The coding agent shall implement **one sprint at a time**.

No dependent sprint shall proceed while the previous required sprint is broken.

## Build Phase Summary

| Phase | Build Phase | Sprints | Primary Outcome |
|---|---|---:|---|
| 1 | Project Foundation and Environment | 5 | Stable Django/PostgreSQL development foundation |
| 2 | Authentication and User Management | 5 | Secure role-based user system |
| 3 | Landlord and Apartment Management | 6 | Complete apartment-listing and verification workflow |
| 4 | Tenant Search, Preferences and Communication | 6 | Tenant discovery, preference and messaging functionality |
| 5 | Weighted KNN Recommendation Engine | 7 | Integrated machine-learning recommendation component |
| 6 | Administration, Security and Integration | 6 | Secure fully integrated application |
| 7 | Testing, Evaluation and Deployment | 7 | Tested, evaluated and deployed system |

**Total: 42 controlled Agile sprints.**

---

# 35. PHASE 1 — PROJECT FOUNDATION AND ENVIRONMENT

## Phase Objective

Establish the complete development environment, source-control workflow, Django foundation, PostgreSQL connection, configuration management and initial application shell.

### Sprint 1.1 — Development Environment Verification

Tasks:

- verify Python installation;
- verify virtual environment;
- verify pip;
- verify Git;
- verify PostgreSQL;
- verify pgAdmin;
- verify OpenCode CLI;
- confirm repository directory;
- confirm `AGENTS.md`;
- confirm this system-requirements document.

Deliverable:

**Verified development workstation and project directory.**

Acceptance criteria:

- Python works inside `.venv`;
- PostgreSQL server is reachable;
- Git is configured;
- OpenCode can read project instructions.

---

### Sprint 1.2 — Project and Repository Initialisation

Tasks:

- initialise Git repository;
- create `.gitignore`;
- create `.env.example`;
- create README;
- establish project documentation;
- create initial branch strategy where required.

Deliverable:

**Version-controlled project foundation.**

---

### Sprint 1.3 — Django Project Initialisation

Tasks:

- install approved dependencies;
- create Django project;
- create modular Django apps;
- configure base settings;
- configure development settings;
- configure URL routing.

Deliverable:

**Running Django application.**

---

### Sprint 1.4 — PostgreSQL Integration

Tasks:

- configure database environment variables;
- connect Django to `landlord_tenant_db`;
- verify migrations;
- test database connectivity;
- configure development database settings.

Deliverable:

**Django-to-PostgreSQL integration.**

---

### Sprint 1.5 — Base UI, Static Files and Foundation Validation

Tasks:

- configure templates;
- configure static files;
- configure media files;
- create base template;
- create navigation structure;
- test application startup;
- run foundation tests;
- document environment setup.

Phase exit criteria:

- application starts successfully;
- PostgreSQL connection works;
- base UI renders;
- project architecture conforms to `AGENTS.md`.

---

# 36. PHASE 2 — AUTHENTICATION AND USER MANAGEMENT

## Phase Objective

Implement secure authentication, role management and user-profile functionality.

### Sprint 2.1 — Custom User Model and Roles

Tasks:

- create custom user model;
- define Tenant/Landlord/Admin roles;
- configure user manager;
- configure migrations;
- register user model with Django Admin.

Deliverable:

**Role-enabled user model.**

---

### Sprint 2.2 — Registration

Tasks:

- tenant registration;
- landlord registration;
- email validation;
- password validation;
- duplicate account prevention;
- API serializer/form validation.

Deliverable:

**Secure registration workflow.**

---

### Sprint 2.3 — Authentication

Tasks:

- login;
- logout;
- JWT configuration where API endpoints require token authentication;
- refresh-token flow;
- secure session handling;
- authentication tests.

Deliverable:

**Working authentication system.**

---

### Sprint 2.4 — Profile Management

Tasks:

- tenant profile;
- landlord profile;
- view profile;
- edit profile;
- contact information;
- profile API/UI.

Deliverable:

**Role-specific profile management.**

---

### Sprint 2.5 — Permissions and Role-Based Access

Tasks:

- Tenant permissions;
- Landlord permissions;
- Administrator permissions;
- ownership permissions;
- protected views;
- protected endpoints;
- permission tests.

Phase exit criteria:

- users can authenticate;
- tenants cannot access landlord/admin functions;
- landlords cannot access admin functions;
- administrator routes are protected.

---

# 37. PHASE 3 — LANDLORD AND APARTMENT MANAGEMENT

## Phase Objective

Implement landlord verification and complete apartment-listing functionality.

### Sprint 3.1 — Landlord Verification Data Model

Tasks:

- create verification model;
- verification status;
- verification remarks;
- submission timestamp;
- administrator relationship.

Deliverable:

**Verification database model.**

---

### Sprint 3.2 — Verification Workflow

Tasks:

- landlord submission;
- pending state;
- admin review;
- approval;
- rejection;
- verification-status UI/API;
- permission tests.

Deliverable:

**Administrative landlord-verification workflow.**

---

### Sprint 3.3 — Apartment Data Model

Tasks:

- apartment model;
- apartment attributes;
- facilities;
- landlord relationship;
- availability;
- validation;
- database indexes where appropriate.

Deliverable:

**Apartment schema and migrations.**

---

### Sprint 3.4 — Apartment Creation and Media

Tasks:

- apartment creation form/API;
- image model;
- image upload;
- upload validation;
- landlord ownership;
- listing validation.

Deliverable:

**Apartment creation functionality.**

---

### Sprint 3.5 — Apartment Update, Delete and Availability

Tasks:

- edit listing;
- delete listing;
- update availability;
- ownership restrictions;
- update media;
- listing status.

Deliverable:

**Apartment-management functionality.**

---

### Sprint 3.6 — Apartment Presentation and Module Testing

Tasks:

- apartment cards;
- apartment details;
- landlord permitted information;
- facilities display;
- availability display;
- module tests.

Phase exit criteria:

- landlords can manage their own apartments;
- tenants can view structured apartment information;
- unauthorized users cannot modify listings.

---

# 38. PHASE 4 — TENANT SEARCH, PREFERENCES AND COMMUNICATION

## Phase Objective

Implement property discovery, tenant preference management and direct landlord-to-tenant communication.

### Sprint 4.1 — Apartment Search

Tasks:

- location search;
- apartment-type search;
- price search;
- bedroom search;
- bathroom search.

Deliverable:

**Basic apartment search.**

---

### Sprint 4.2 — Combined Filtering

Tasks:

- price range;
- location;
- apartment type;
- bedrooms;
- bathrooms;
- facilities;
- availability;
- pagination.

Deliverable:

**Combined filtering system.**

---

### Sprint 4.3 — Tenant Preference Model

Tasks:

- create preference model;
- preference fields;
- validation;
- tenant relationship;
- migrations.

Deliverable:

**Persistent tenant-preference model.**

---

### Sprint 4.4 — Preference Management UI/API

Tasks:

- create preference;
- retrieve preference;
- update preference;
- validate preference;
- prepare preference information for recommendation service.

Deliverable:

**Tenant-preference management.**

---

### Sprint 4.5 — Messaging and Conversations

Tasks:

- conversation model;
- message model;
- send message;
- receive message;
- conversation history;
- message permissions.

Deliverable:

**Direct tenant-landlord messaging.**

---

### Sprint 4.6 — Tenant Journey Integration

Tasks:

- integrate search;
- apartment details;
- preferences;
- landlord contact;
- messages;
- run tenant-flow integration tests.

Phase exit criteria:

```text
Tenant
  ↓
Search
  ↓
Filter
  ↓
View Apartment
  ↓
Save Preferences
  ↓
Contact Landlord
```

must work successfully.

---

# 39. PHASE 5 — WEIGHTED KNN RECOMMENDATION ENGINE

## Phase Objective

Implement the approved Weighted KNN recommendation component and integrate it with actual PostgreSQL apartment records and tenant preferences.

### Sprint 5.1 — Recommendation Feature Specification

Tasks:

- confirm final feature list;
- map database fields to ML features;
- classify numerical/categorical/binary attributes;
- define hard filters;
- define configurable feature weights.

Deliverable:

**Recommendation feature specification.**

---

### Sprint 5.2 — Feature Extraction and Encoding

Tasks:

- tenant-vector construction;
- apartment-vector construction;
- categorical encoding;
- binary feature encoding;
- missing-value handling;
- preprocessing tests.

Deliverable:

**Feature-processing pipeline.**

---

### Sprint 5.3 — Numerical Normalisation

Tasks:

- implement min-max normalisation;
- protect against division by zero;
- normalise eligible apartment data;
- normalise tenant numerical preferences;
- write deterministic tests.

Deliverable:

**Tested normalisation service.**

---

### Sprint 5.4 — Feature Weighting and Weighted Distance

Tasks:

- implement weight configuration;
- implement weighted Euclidean distance;
- validate mathematical correctness;
- create known numerical test cases.

Deliverable:

**Weighted-distance engine.**

---

### Sprint 5.5 — KNN Candidate Selection and Ranking

Tasks:

- retrieve eligible apartments;
- apply hard filters;
- calculate distances;
- sort ascending;
- select K nearest candidates;
- assign ranking positions;
- test limited-candidate cases.

Deliverable:

**Weighted KNN ranking engine.**

---

### Sprint 5.6 — Django/API/UI Recommendation Integration

Tasks:

- recommendation service layer;
- recommendation API;
- preference-to-recommendation flow;
- recommendation results page;
- recommendation-record persistence where required;
- error handling.

Deliverable:

**Integrated recommendation feature.**

---

### Sprint 5.7 — Recommendation Validation and Evaluation Readiness

Tasks:

- validate hard-filter behaviour;
- validate feature weighting;
- validate ranking;
- validate K configuration;
- validate missing-data handling;
- create reproducible test scenarios;
- prepare evaluation dataset/test cases.

Phase exit criteria:

- actual apartment records are ranked;
- no fake recommendation scores are used;
- lower weighted distance results in higher ranking;
- the algorithm is reproducible and testable.

---

# 40. PHASE 6 — ADMINISTRATION, SECURITY AND SYSTEM INTEGRATION

## Phase Objective

Complete administrative functionality, security hardening, auditing and system-wide integration.

### Sprint 6.1 — Administrator Dashboard

Tasks:

- user management;
- landlord management;
- apartment management;
- verification overview;
- system overview.

Deliverable:

**Administrative dashboard.**

---

### Sprint 6.2 — Administrative Workflows

Tasks:

- user status management;
- apartment moderation;
- verification administration;
- administrative reports;
- administrator permissions.

Deliverable:

**Complete administrative workflows.**

---

### Sprint 6.3 — Security Hardening

Tasks:

- verify password security;
- verify CSRF protection;
- validate permissions;
- secure cookies configuration;
- validate file uploads;
- secure error responses;
- review secrets management.

Deliverable:

**Hardened application configuration.**

---

### Sprint 6.4 — API Security and Validation

Tasks:

- serializer validation;
- authorization;
- JWT protections;
- throttling where appropriate;
- pagination;
- consistent error responses;
- API permission tests.

Deliverable:

**Secured REST API.**

---

### Sprint 6.5 — Audit, Logging and Data Integrity

Tasks:

- administrative audit events;
- relevant login/activity logging;
- database constraints;
- referential-integrity review;
- deletion behaviour;
- error logging.

Deliverable:

**Operational controls and audit foundation.**

---

### Sprint 6.6 — Full System Integration

Tasks:

- execute full user flows;
- verify module interoperability;
- resolve integration defects;
- execute regression tests;
- review architecture compliance.

Phase exit criteria:

all major modules function together without bypassing role, data or security rules.

---

# 41. PHASE 7 — TESTING, EVALUATION AND DEPLOYMENT

## Phase Objective

Validate, evaluate, optimise and deploy the completed system while collecting real evidence for the academic project.

### Sprint 7.1 — Unit Testing

Test:

- models;
- forms;
- serializers;
- services;
- permissions;
- recommendation functions;
- preprocessing functions.

Deliverable:

**Unit-test suite.**

---

### Sprint 7.2 — Integration and API Testing

Test:

- registration/login;
- landlord/apartment;
- tenant/preferences;
- preferences/recommendation;
- tenant/landlord messaging;
- administrator/verification;
- REST API endpoints.

Deliverable:

**Integration/API test results.**

---

### Sprint 7.3 — System and End-to-End Testing

Tenant journey:

```text
Register
  ↓
Login
  ↓
Search
  ↓
Filter
  ↓
Preferences
  ↓
Recommendation
  ↓
Apartment Details
  ↓
Message Landlord
```

Landlord journey:

```text
Register
  ↓
Verification
  ↓
Create Apartment
  ↓
Manage Apartment
  ↓
Receive Message
```

Administrator journey:

```text
Login
  ↓
Manage Users
  ↓
Review Verification
  ↓
Manage Listings
```

Deliverable:

**End-to-end system-test evidence.**

---

### Sprint 7.4 — Security and Performance Testing

Tasks:

- unauthorized-access tests;
- input-validation tests;
- authentication tests;
- permission tests;
- file-upload tests;
- response-time measurement;
- recommendation response-time measurement.

Deliverable:

**Security and performance results.**

---

### Sprint 7.5 — User Acceptance and Usability Evaluation

Evaluate:

- registration;
- navigation;
- apartment search;
- apartment information;
- recommendation interface;
- messaging;
- overall usability.

Only actual participant/test results shall be documented.

Deliverable:

**User-acceptance/usability evidence.**

---

### Sprint 7.6 — Weighted KNN Evaluation

Evaluate:

- recommendation relevance;
- ranking correctness;
- K behaviour;
- weighting behaviour;
- response time;
- controlled preference scenarios;
- recommendation metrics where suitable data permits.

Deliverable:

**ML evaluation results for Chapter Four.**

---

### Sprint 7.7 — Production Deployment and Finalisation

Tasks:

- configure production settings;
- configure managed PostgreSQL;
- configure environment variables;
- configure static files;
- deploy Django application;
- apply migrations;
- run deployment checks;
- verify production functionality;
- prepare backups/logging;
- update README;
- prepare Chapter Four implementation evidence.

Phase exit criteria:

- deployed system is accessible;
- production checks pass;
- database functions;
- major user journeys function;
- real screenshots/test results are available for documentation.

---

# 42. SPRINT GOVERNANCE

Every sprint shall follow:

```text
Sprint Planning
      ↓
Requirement Review
      ↓
Implementation
      ↓
Testing
      ↓
Defect Correction
      ↓
Sprint Review
      ↓
Documentation
      ↓
Approval
      ↓
Next Sprint
```

Sprint rules:

1. Implement one controlled sprint at a time.
2. Inspect existing code before modification.
3. State planned changes before implementation.
4. Do not introduce out-of-scope features.
5. Write relevant tests.
6. Run tests before completion.
7. Record database migrations.
8. Document API changes.
9. Validate security implications.
10. Validate ML changes mathematically where relevant.
11. Do not proceed to dependent work when a sprint is broken.
12. Make meaningful Git commits.
13. Update documentation after substantial changes.

---

# 43. SPRINT DEFINITION OF DONE

A sprint or feature is complete only when applicable requirements are satisfied:

```text
[ ] Code implemented
[ ] Database migrations completed
[ ] Validation implemented
[ ] Permissions implemented
[ ] Relevant tests written
[ ] Tests executed successfully
[ ] UI/API verified
[ ] Error handling verified
[ ] Documentation updated
[ ] Security impact checked
[ ] AGENTS.md compliance checked
[ ] Git commit created
```

---

# 44. PHASE-TO-REQUIREMENT TRACEABILITY

| Phase | Requirements Addressed | Main Deliverable |
|---|---|---|
| Phase 1 | Infrastructure, configuration, database connectivity | Stable project foundation |
| Phase 2 | Registration, authentication, roles, profiles | User-management system |
| Phase 3 | Landlord verification and apartment listings | Property-management system |
| Phase 4 | Search, filters, preferences, messaging | Tenant-discovery workflow |
| Phase 5 | Weighted KNN recommendation | ML recommendation engine |
| Phase 6 | Administration, security and integration | Secure integrated platform |
| Phase 7 | Testing, ML evaluation and deployment | Evaluated production-ready academic prototype |

---

# 45. IMPLEMENTATION ROADMAP

```text
PHASE 1
Project Foundation
5 Sprints
    ↓
PHASE 2
Authentication & Users
5 Sprints
    ↓
PHASE 3
Landlord & Apartment Management
6 Sprints
    ↓
PHASE 4
Search, Preferences & Messaging
6 Sprints
    ↓
PHASE 5
Weighted KNN Recommendation
7 Sprints
    ↓
PHASE 6
Administration, Security & Integration
6 Sprints
    ↓
PHASE 7
Testing, Evaluation & Deployment
7 Sprints
    ↓
FINAL SYSTEM
```

---

# 46. PRODUCTION CONFIGURATION

Production configuration shall include:

```text
DEBUG=False
Secure SECRET_KEY
Managed PostgreSQL credentials
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
HTTPS
Secure cookies
Static-file configuration
Media-file configuration
Logging
Backups
```

Recommended server configuration:

- Gunicorn;
- WhiteNoise where appropriate;
- Nginx where self-managed infrastructure is used;
- Render or equivalent managed deployment environment.

Production database migrations shall be run using Django migrations.

---

# 47. GIT WORKFLOW

Recommended branches:

```text
main
develop
feature/*
```

Examples:

```text
feature/authentication
feature/apartments
feature/preferences
feature/recommendations
feature/messaging
feature/verification
```

Commit examples:

```text
feat: implement custom user model
feat: add apartment listing workflow
feat: implement tenant preferences
feat: implement weighted knn ranking
test: add weighted distance tests
fix: enforce landlord apartment ownership
docs: update system requirements
```

---

# 48. DOCUMENTATION REQUIREMENTS

The repository shall maintain:

- `AGENTS.md`;
- `SYSTEM_REQUIREMENTS.md`;
- `README.md`;
- `.env.example`;
- API documentation;
- installation instructions;
- testing instructions;
- recommendation-engine description;
- deployment instructions.

Actual implementation shall remain traceable to the approved academic design.

---

# 49. ACADEMIC ALIGNMENT

The implementation must remain aligned with:

## Chapter One

- research problem;
- aim;
- objectives;
- project scope.

## Chapter Two

- literature review;
- research gap;
- recommendation methodology;
- Weighted KNN selection.

## Chapter Three

- system analysis;
- Agile methodology;
- OOAD;
- logical design;
- physical design;
- program specification;
- database design;
- system controls.

## Chapter Four

Shall report only the implementation actually built, including:

- development environment;
- implemented modules;
- screenshots;
- database implementation;
- Weighted KNN implementation;
- tests;
- evaluation results.

## Chapter Five

Shall be based on actual project outcomes.

No implementation result, test result, user result, performance metric or ML metric shall be fabricated.

---

# 50. FINAL ARCHITECTURE

```text
                    WEB BROWSER
                         │
                       HTTPS
                         │
                         ▼
                 PRESENTATION LAYER
           Django Templates / HTML / CSS / JS
                         │
                         ▼
                  DJANGO APPLICATION
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
     Accounts        Apartments       Messaging
        │                │                 │
        └────────────────┼─────────────────┘
                         │
              ┌──────────┴───────────┐
              ▼                      ▼
         Verification          Recommendation
                                      │
                                      ▼
                                Weighted KNN
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  Tenant Preferences       Apartment Features
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                                Preprocessing
                                      │
                                      ▼
                                 Weighting
                                      │
                                      ▼
                              Weighted Distance
                                      │
                                      ▼
                              K Nearest Candidates
                                      │
                                      ▼
                                   Ranking
                                      │
                                      ▼
                              Recommendations
                                      │
                                      ▼
                                PostgreSQL 18
```

---

# 51. AUTHORITATIVE IMPLEMENTATION RULE

The approved implementation chain is:

```text
Agile
  ↓
OOAD
  ↓
Python / Django
  ↓
Django REST Framework
  ↓
PostgreSQL
  ↓
Weighted KNN
  ↓
Testing and Evaluation
  ↓
Production Deployment
```

This architecture shall not be materially changed without explicit project-owner approval.

`AGENTS.md` shall govern coding-agent behaviour, while this document shall govern what the system is required to implement.
