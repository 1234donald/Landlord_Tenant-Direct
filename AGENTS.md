\# AGENTS.md

\# LANDLORD–TENANT PLATFORM

\## NON-NEGOTIABLE DEVELOPMENT RULES

This document defines the mandatory rules, architecture, technology choices,

development methodology, ML methodology, security requirements, scope

limitations, and implementation workflow for this project.

The AI coding agent MUST follow these rules throughout the entire project.

---

\# 1. PROJECT IDENTITY

Project Title:

"Design and Implementation of an Online Platform for Direct

Landlord-to-Tenant Contact Using Artificial Intelligence and

Machine Learning Techniques"

The system is a web-based landlord–tenant platform designed to:

1\. Allow prospective tenants to search for residential apartments.

2\. Allow landlords to register and manage apartment listings.

3\. Allow tenants and landlords to communicate directly.

4\. Allow administrators to manage users and listings.

5\. Provide an administrative landlord-verification workflow.

6\. Provide personalised apartment recommendations using Weighted KNN.

---

\# 2. PRIMARY DEVELOPMENT OBJECTIVE

The objective is to implement the actual system described in the academic

project documentation.

DO NOT redesign the project around a different concept.

DO NOT replace the selected ML methodology.

DO NOT add unrelated functionality merely because it is technically possible.

The implementation must remain aligned with the project's approved scope,

objectives, Chapter One, Chapter Two and Chapter Three.

---

\# 3. DEVELOPMENT METHODOLOGY

The project follows:

AGILE DEVELOPMENT

\+

OBJECT-ORIENTED ANALYSIS AND DESIGN (OOAD)

IMPORTANT:

\- Agile is the SOFTWARE DEVELOPMENT METHODOLOGY.

\- OOAD is the SYSTEM ANALYSIS AND DESIGN APPROACH.

\- Do not describe OOAD as the development methodology.

\- Do not replace Agile with another development methodology without explicit

approval from the project owner.

Development must proceed incrementally.

Each major feature must be implemented, tested and verified before moving to

the next major feature.

---

\# 4. MANDATORY TECHNOLOGY STACK

The primary stack is:

Backend:

\- Python

\- Django

\- Django REST Framework where an API layer is required

Database:

\- PostgreSQL

Frontend:

\- HTML5

\- CSS3

\- JavaScript

\- Django Templates unless a separate frontend is explicitly approved

Machine Learning:

\- Python

\- NumPy

\- pandas

\- scikit-learn where appropriate

\- custom Weighted KNN logic where required

Development:

\- Visual Studio Code

\- Git

\- GitHub

Environment:

\- Python virtual environment (.venv)

Production:

\- Linux-based deployment

\- Gunicorn

\- Nginx

\- PostgreSQL

\- HTTPS

\- environment variables

---

\# 5. TECHNOLOGY RESTRICTION

Do not introduce additional frameworks, databases or programming languages

without explicit approval.

DO NOT replace:

\- Django with Flask

\- Django with FastAPI

\- PostgreSQL with MySQL

\- PostgreSQL with SQLite for production

\- Weighted KNN with collaborative filtering

\- Weighted KNN with a neural network

\- Weighted KNN with a recommendation API

\- HTML/CSS/JavaScript with React unless explicitly approved

Additional libraries may only be introduced when they provide a clear,

necessary function and do not conflict with the approved architecture.

Prefer Django's built-in functionality where practical.

---

\# 6. ARCHITECTURE

The system must follow a layered architecture.

CLIENT

\|

v

PRESENTATION LAYER

HTML/CSS/JavaScript

\|

v

APPLICATION LAYER

Django

\|

+------------+------------+

\| \| \|

v v v

Business REST ML/Recommendation

Logic API Component

\| \|

+------------+------------+

\|

v

DATA LAYER

PostgreSQL

The system must maintain clear separation between:

\- presentation

\- business logic

\- data access

\- recommendation logic

\- authentication/authorization

Do not place complex business logic directly inside templates.

Do not place database logic directly inside templates.

Do not place the complete recommendation algorithm inside views.

---

\# 7. DJANGO PROJECT STRUCTURE

Use a modular Django structure.

Recommended structure:

landlord_tenant_project/

│

├── manage.py

│

├── config/

│ ├── settings/

│ ├── urls.py

│ ├── asgi.py

│ └── wsgi.py

│

├── apps/

│ ├── accounts/

│ ├── apartments/

│ ├── recommendations/

│ ├── messaging/

│ ├── verification/

│ └── core/

│

├── templates/

├── static/

├── media/

├── ml/

├── tests/

├── requirements/

├── .env.example

├── .gitignore

├── README.md

└── AGENTS.md

The exact structure may be adjusted when implementation requires it, but

functional separation must be maintained.

---

\# 8. USER ROLES

The system has exactly three primary roles:

1\. Tenant

2\. Landlord

3\. Administrator

Role-based access control is mandatory.

TENANT:

\- search apartments

\- filter apartments

\- view apartment details

\- enter preferences

\- receive recommendations

\- communicate with landlords

\- manage own profile

LANDLORD:

\- register

\- manage profile

\- submit verification information

\- create listings

\- edit listings

\- manage availability

\- communicate with tenants

ADMINISTRATOR:

\- manage users

\- review landlord verification

\- approve/reject verification

\- manage apartment listings

\- monitor system

\- access administrative information

Users must not be able to access functionality belonging to another role

unless explicitly authorised.

---

\# 9. LANDLORD VERIFICATION

Landlord verification is an ADMINISTRATIVE workflow.

Required workflow:

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

IMPORTANT:

The system MUST NOT claim that it legally verifies property ownership.

The system MUST NOT make legal determinations.

The system's verification mechanism is an administrative platform control.

---

\# 10. APARTMENT LISTINGS

Apartment listings should support, where applicable:

\- location

\- rental price

\- apartment type

\- bedrooms

\- bathrooms

\- facilities

\- description

\- availability

\- images/media

\- landlord relationship

\- verification/listing status

Listings must be validated before being stored.

Required fields must not silently accept invalid data.

Rental price must be numeric and positive.

Bedroom and bathroom counts must be valid numeric values.

---

\# 11. RECOMMENDATION METHODOLOGY

THIS IS NON-NEGOTIABLE.

The recommendation algorithm is:

WEIGHTED K-NEAREST NEIGHBOUR (WEIGHTED KNN)

Do not replace it with:

\- collaborative filtering

\- matrix factorisation

\- neural networks

\- deep learning

\- reinforcement learning

\- generic content-based filtering

\- an external recommendation API

\- an unrelated hybrid recommender

The project's intelligent recommendation mechanism must remain

Weighted KNN with feature weighting.

---

\# 12. RECOMMENDATION DESIGN

Tenant preferences form the query vector:

U = (u1, u2, ..., un)

Apartment characteristics form candidate vectors:

A = (a1, a2, ..., an)

The weighted Euclidean distance is:

Dw(U,A) = sqrt(Σ wi(ui - ai)^2)

where:

wi = feature weight

ui = tenant preference value

ai = apartment feature value

Smaller distance means greater similarity.

Recommendations must therefore be ranked:

LOWEST DISTANCE → HIGHEST RELEVANCE

---

\# 13. RECOMMENDATION FEATURES

Potential features include:

\- rental price

\- location

\- apartment type

\- bedrooms

\- bathrooms

\- parking

\- electricity

\- water

\- security

\- furnished/unfurnished status

\- other relevant facilities

The final feature set must correspond to the database schema and project

documentation.

Do not create ML features that cannot be obtained from the actual system.

---

\# 14. FEATURE PROCESSING

Before calculating distance:

1\. Validate tenant preferences.

2\. Retrieve eligible apartments.

3\. Apply mandatory/hard filters.

4\. Encode categorical variables where necessary.

5\. Normalise numerical variables.

6\. Apply feature weights.

7\. Calculate weighted distance.

8\. Rank apartments.

9\. Return recommendations.

Numerical normalisation may use:

x' = (x - xmin) / (xmax - xmin)

The implementation must avoid division-by-zero when a feature has identical

minimum and maximum values.

---

\# 15. HARD FILTERS VS ML RANKING

The system must distinguish between:

HARD FILTERING

and

ML SIMILARITY RANKING.

Example:

If the tenant specifies:

Maximum rent = ₦500,000

an apartment costing ₦900,000 should not be recommended merely because its

other attributes are similar.

Mandatory constraints should be applied before recommendation ranking where

appropriate.

Weighted KNN should primarily rank eligible candidates.

---

\# 16. K VALUE

The recommendation system must support a configurable K value.

Do not arbitrarily hard-code K without documenting the reason.

K should be configurable through application settings or the recommendation

service where practical.

The selected value must be documented and evaluated during testing.

---

\# 17. MACHINE LEARNING CLAIMS

Do not make unsupported claims.

The system must NOT claim:

\- human-level intelligence

\- perfect recommendations

\- guaranteed best apartments

\- guaranteed tenant satisfaction

\- legally verified properties

\- guaranteed property ownership

\- fraud-proof listings

The recommendation system provides similarity-based recommendations based on

available structured data and stated tenant preferences.

---

\# 18. DATABASE

PostgreSQL is the production database.

Core entities should include, where applicable:

\- User

\- Tenant

\- Landlord

\- Apartment

\- Preference

\- Recommendation

\- Message

\- Verification

Use appropriate:

\- primary keys

\- foreign keys

\- indexes

\- constraints

\- unique constraints

\- timestamps

Do not duplicate data unnecessarily.

Database relationships must reflect actual business rules.

---

\# 19. SECURITY

Security is mandatory.

Implement:

\- password hashing

\- Django authentication

\- CSRF protection

\- role-based authorization

\- input validation

\- secure session handling

\- secure cookies in production

\- protection against SQL injection

\- protection against XSS

\- protection against CSRF

\- environment variables for secrets

\- DEBUG=False in production

\- secure SECRET_KEY handling

\- appropriate ALLOWED_HOSTS

\- HTTPS in production

Never hard-code:

\- SECRET_KEY

\- database passwords

\- API keys

\- email credentials

\- production credentials

inside source code.

---

\# 20. ENVIRONMENT VARIABLES

Use environment variables.

Required examples:

SECRET_KEY=

DEBUG=

DATABASE_URL=

DB_NAME=

DB_USER=

DB_PASSWORD=

DB_HOST=

DB_PORT=

ALLOWED_HOSTS=

Use:

.env

for local development.

Provide:

.env.example

without real credentials.

Never commit .env to Git.

---

\# 21. API DESIGN

Where APIs are implemented, use a clean REST-oriented structure.

Example:

/api/v1/auth/

/api/v1/users/

/api/v1/apartments/

/api/v1/preferences/

/api/v1/recommendations/

/api/v1/messages/

/api/v1/verification/

Use:

\- appropriate HTTP methods

\- meaningful status codes

\- validation

\- authentication

\- authorization

\- consistent JSON responses

Do not create unnecessary APIs simply for the sake of having APIs.

---

\# 22. ERROR HANDLING

The application must fail gracefully.

Do not expose:

\- stack traces

\- database credentials

\- secret keys

\- internal paths

\- sensitive system information

to normal users.

Errors must be logged appropriately.

User-facing errors must be understandable.

---

\# 23. INPUT VALIDATION

Validate all user-controlled input.

Validation must occur at the appropriate layers.

Examples:

\- email format

\- password requirements

\- price

\- bedroom count

\- bathroom count

\- apartment type

\- required fields

\- message content

\- preference values

\- uploaded files

Never trust client-side validation alone.

Server-side validation is mandatory.

---

\# 24. FILE UPLOADS

Apartment images/media must be validated.

Consider:

\- file type

\- file size

\- filename handling

\- storage location

Do not allow arbitrary executable files to be uploaded.

Media files must not be treated as executable code.

---

\# 25. CODE QUALITY

Write maintainable code.

Requirements:

\- meaningful variable names

\- meaningful function names

\- small focused functions

\- reusable components

\- comments only where useful

\- no unnecessary duplication

\- no dead code

\- no placeholder implementations disguised as completed features

Follow Python and Django conventions.

---

\# 26. TESTING

Testing is mandatory.

Implement tests for:

\- authentication

\- authorization

\- user registration

\- landlord registration

\- apartment creation

\- apartment editing

\- apartment deletion

\- apartment search

\- filtering

\- messaging

\- landlord verification

\- recommendation logic

\- feature preprocessing

\- weighted distance calculation

\- recommendation ranking

\- invalid input

\- permission restrictions

The project must not be considered complete merely because the application

starts successfully.

---

\# 27. ML TESTING

The recommendation component must have dedicated tests.

At minimum verify:

1\. Correct feature construction.

2\. Correct normalisation.

3\. Correct weight application.

4\. Correct weighted-distance calculation.

5\. Correct ascending ranking.

6\. Correct handling of missing/invalid values.

7\. Correct hard-filter behaviour.

8\. Correct K behaviour.

9\. Stable behaviour when candidate apartments are limited.

Include numerical test cases where the expected distance/ranking is known.

---

\# 28. TESTING AND EVALUATION

The system must be evaluated using measurable criteria.

Examples:

\- functional correctness

\- recommendation ranking behaviour

\- recommendation relevance

\- response time

\- usability

\- security controls

\- successful completion of major use cases

Do not invent test results.

Only report results obtained from actual execution.

---

\# 29. GIT

Git must be used throughout development.

Use meaningful commits.

Examples:

feat: implement tenant registration

feat: implement landlord verification

feat: add apartment listing module

feat: implement weighted knn recommendation

test: add recommendation tests

fix: correct apartment filtering

docs: update system architecture

Do not make one enormous commit containing the entire project unless absolutely

necessary.

---

\# 30. IMPLEMENTATION WORKFLOW

The agent MUST NOT attempt to build the entire project in one uncontrolled

operation.

Follow this order:

PHASE 1

Environment verification

PHASE 2

Project initialization

PHASE 3

Django configuration

PHASE 4

PostgreSQL integration

PHASE 5

Authentication and user roles

PHASE 6

Tenant module

PHASE 7

Landlord module

PHASE 8

Apartment listing module

PHASE 9

Search and filtering

PHASE 10

Landlord verification

PHASE 11

Messaging

PHASE 12

Recommendation data model

PHASE 13

Weighted KNN implementation

PHASE 14

Recommendation UI/API integration

PHASE 15

Administration

PHASE 16

Security hardening

PHASE 17

Testing

PHASE 18

Documentation

PHASE 19

Production configuration

PHASE 20

Deployment preparation

---

\# 31. PHASE CONTROL

Before starting each phase:

1\. Inspect the existing code.

2\. Identify dependencies.

3\. State what will be changed.

4\. Implement only that phase.

5\. Run relevant tests.

6\. Fix errors.

7\. Verify functionality.

8\. Review against this AGENTS.md.

9\. Commit the completed work.

Do not proceed to the next major phase when the current phase is broken.

---

\# 32. EXISTING CODE RULE

Before modifying an existing file:

\- inspect it first

\- understand its purpose

\- preserve working functionality

\- make the smallest appropriate change

Do not rewrite working code unnecessarily.

Do not delete existing functionality without justification.

---

\# 33. DATABASE MIGRATIONS

Django migrations must be used.

Do not manually modify production database schemas unless explicitly

required.

After model changes:

python manage.py makemigrations

then:

python manage.py migrate

Migration files must be committed to Git.

---

\# 34. ADMIN INTERFACE

Use Django Admin where appropriate for administrative management.

The admin interface should support:

\- users

\- landlords

\- tenants

\- apartments

\- verification records

\- recommendations where useful

\- messages where appropriate

Do not expose sensitive information unnecessarily.

---

\# 35. DOCUMENTATION

Maintain:

README.md

The README should eventually contain:

\- project description

\- technology stack

\- installation instructions

\- environment setup

\- database setup

\- migration instructions

\- development commands

\- testing commands

\- ML recommendation explanation

\- deployment instructions

---

\# 36. ACADEMIC PROJECT ALIGNMENT

The implementation must remain consistent with the academic project.

The following must remain aligned:

Chapter One:

\- problem

\- aim

\- objectives

\- scope

Chapter Two:

\- literature-supported methodology

\- recommendation approach

\- research gap

Chapter Three:

\- system analysis

\- Agile development methodology

\- OOAD design approach

\- logical design

\- physical design

\- Weighted KNN design

Chapter Four:

\- actual implementation

\- screenshots

\- testing

\- results

\- evaluation

Chapter Five:

\- summary

\- conclusion

\- recommendations

\- future work

Never implement a major feature that cannot be justified within the approved

academic scope.

---

\# 37. STRICT PROJECT SCOPE

The system DOES:

\- facilitate landlord-to-tenant contact

\- manage apartment listings

\- provide apartment search

\- provide apartment filtering

\- provide personalised apartment recommendations

\- manage users

\- provide landlord verification workflow

\- provide messaging

The system DOES NOT:

\- legally verify property ownership

\- verify government land documents

\- process rent payments

\- sign tenancy agreements

\- manage property maintenance

\- replace estate agents as a legal profession

\- act as a legal authority

\- make legal property decisions

\- guarantee that a landlord is the legal owner

\- guarantee that an apartment is free from fraud

Do not implement these excluded functions unless explicitly approved.

---

\# 38. NO FEATURE CREEP

Do not independently add:

\- payment gateway

\- cryptocurrency

\- blockchain

\- facial recognition

\- biometric authentication

\- advanced deep learning

\- chatbot

\- social network

\- property ownership blockchain

\- automated legal verification

\- credit scoring

\- insurance

\- unnecessary microservices

unless explicitly requested and approved.

---

\# 39. NO FAKE IMPLEMENTATION

NEVER create:

\- fake recommendation scores

\- random recommendation results

\- fake verification statuses

\- fake user statistics

\- fabricated test results

\- fabricated performance metrics

\- placeholder ML results presented as real results

If something has not been implemented, clearly state:

NOT IMPLEMENTED

If something is incomplete, clearly state:

INCOMPLETE

---

\# 40. NO FABRICATED DATA

Development seed data may be created for testing.

However:

\- clearly identify it as test/demo data

\- never present test data as real-world data

\- never fabricate evaluation results

\- never fabricate user feedback

\- never fabricate recommendation accuracy

---

\# 41. RECOMMENDATION DATA

The recommendation engine must operate on actual apartment records stored in

the database.

Do not create a separate hidden apartment dataset solely to make the

recommendation system appear functional.

---

\# 42. FRONTEND REQUIREMENTS

The interface should be:

\- responsive

\- simple

\- accessible

\- consistent

\- professional

\- appropriate for an academic project

Important interfaces include:

Tenant:

\- registration

\- login

\- dashboard

\- apartment search

\- apartment details

\- preference form

\- recommendation results

\- messages

Landlord:

\- registration

\- login

\- dashboard

\- profile

\- verification submission

\- apartment management

\- messages

Administrator:

\- dashboard

\- users

\- landlords

\- verification

\- apartments

\- system management

---

\# 43. RECOMMENDATION RESULT UI

Recommendation results should clearly communicate:

\- apartment

\- location

\- rental price

\- relevant characteristics

\- recommendation ranking

\- similarity/distance information where appropriate

Avoid presenting the recommendation as an absolute guarantee.

Use terminology such as:

"Recommended for you"

"Preference match"

"Similarity score"

rather than:

"Guaranteed best property"

---

\# 44. PRODUCTION DEPLOYMENT

Production architecture should follow:

Internet

\|

HTTPS

\|

Nginx

\|

Gunicorn

\|

Django

\|

PostgreSQL

Static files:

Nginx → static files

Media:

Configured persistent media storage

Production requirements:

\- DEBUG=False

\- environment variables

\- PostgreSQL

\- Gunicorn

\- Nginx

\- HTTPS

\- secure cookies

\- allowed hosts

\- static/media configuration

\- database backups

\- logging

---

\# 45. LOCAL DEVELOPMENT

Local development should use:

Windows 11

Python

Git

VS Code

PostgreSQL

Django

Virtual Environment

Always activate the project's virtual environment before installing or

running project dependencies.

Do not install project dependencies globally unless specifically required.

---

\# 46. DEPENDENCY MANAGEMENT

Maintain:

requirements.txt

or an appropriately structured requirements directory.

Dependencies must be pinned or constrained appropriately for reproducibility.

After adding a dependency:

1\. install it

2\. test it

3\. update dependency documentation

4\. verify that it does not conflict with the architecture

---

\# 47. AGENT BEHAVIOUR

The coding agent must:

\- inspect before modifying

\- plan before implementing

\- implement incrementally

\- test after implementation

\- explain errors clearly

\- avoid unnecessary changes

\- preserve project scope

\- follow the approved architecture

\- follow the approved ML methodology

\- maintain documentation

The agent must NOT:

\- silently change architecture

\- silently change frameworks

\- silently change the ML algorithm

\- silently change database technology

\- delete project files without justification

\- fabricate implementation results

\- claim tests passed when they were not run

\- claim deployment succeeded when it was not verified

---

\# 48. WHEN UNCERTAIN

If a decision would materially change:

\- architecture

\- database structure

\- ML methodology

\- project scope

\- security model

\- deployment architecture

\- academic methodology

STOP and ask for approval.

For minor implementation decisions, choose the simplest solution consistent

with this document.

---

\# 49. DEFINITION OF DONE

A feature is NOT complete merely because code exists.

A feature is considered complete only when:

\[ \] Code implemented

\[ \] Database changes migrated

\[ \] Validation implemented

\[ \] Authorization verified

\[ \] Relevant tests written

\[ \] Tests pass

\[ \] UI/API verified

\[ \] Error handling implemented

\[ \] Documentation updated

\[ \] Git commit created

\[ \] AGENTS.md rules checked

---

\# 50. FINAL NON-NEGOTIABLE RULE

The agent's priority is:

CORRECTNESS

\>

PROJECT SCOPE

\>

SECURITY

\>

MAINTAINABILITY

\>

ACADEMIC ALIGNMENT

\>

FEATURE COMPLETENESS

\>

CONVENIENCE

When in doubt, do not guess.

Inspect the project, explain the uncertainty, and request approval when the

decision could affect the architecture, methodology, ML approach or project

scope.
