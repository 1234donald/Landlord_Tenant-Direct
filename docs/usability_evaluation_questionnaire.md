# User Acceptance & Usability Evaluation Questionnaire (Sprint 7.5)

This instrument collects the hands-on **user-acceptance / usability evidence**
for Sprint 7.5 of the Landlord-Tenant Direct Connect Platform. It is the
human-administered companion to the automated live-system suite in
`tests/integration/test_usability_evaluation.py`.

> **Honesty rule (AGENTS 39, 40):** Only record ratings and comments that
> reflect tasks you *actually performed* against the running application. Do
> not invent participants, responses or results. Each response must be entered
> by a real person after really using the system.

---

## How to use this form

1. Start the application locally (`python manage.py runserver`).
2. Perform each task below on the real, running system.
3. Record a rating for **each** statement using the scale:
   **1 = Strongly disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly agree**.
4. Add short notes for any "Disagree/Strongly disagree" rating.
5. Fill in the participant details at the end and save this document as part of
   the Chapter Four evaluation evidence.

---

## Participant details

| Field                | Entry |
|----------------------|-------|
| Participant name     |       |
| Role (tenant/landlord/admin/reviewer) | |
| Date                 |       |
| Environment (`runserver` URL) | |

---

## A. Registration

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| A1 | Registering as a new user is straightforward. |   |   |   |   |   |
| A2 | The success/error feedback after registration clearly explains the outcome. |   |   |   |   |   |
| A3 | I could complete registration without confusion about required fields. |   |   |   |   |   |

Notes:

---

## B. Navigation

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| B1 | The main navigation is consistent across pages. |   |   |   |   |   |
| B2 | Links appropriate to my role are visible (e.g. landlord "My Apartments", tenant "Recommendations", admin "Admin"). |   |   |   |   |   |
| B3 | I could reach every major area without broken links. |   |   |   |   |   |

Notes:

---

## C. Apartment Search

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| C1 | The search page offers the filters I expect (location, type, price, bedrooms, bathrooms, facilities). |   |   |   |   |   |
| C2 | Filtering returned the expected apartments. |   |   |   |   |   |
| C3 | Search result cards clearly show the key details at a glance. |   |   |   |   |   |

Notes:

---

## D. Apartment Information

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| D1 | The apartment detail page shows all important information (title, price, location, type, bedrooms, bathrooms, facilities, description). |   |   |   |   |   |
| D2 | Landlord contact details are easy to find. |   |   |   |   |   |
| D3 | The page layout is readable and well structured. |   |   |   |   |   |

Notes:

---

## E. Recommendation Interface

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| E1 | I understand that apartments are ranked by how closely they match my preferences. |   |   |   |   |   |
| E2 | Ranking (rank number) and similarity score are clearly displayed. |   |   |   |   |   |
| E3 | The recommendations were relevant to my stated preferences. |   |   |   |   |   |
| E4 | The wording is factual and does not over-promise (e.g. no "guaranteed best"). |   |   |   |   |   |

Notes:

---

## F. Messaging

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| F1 | I could start contact with the other party (tenant ↔ landlord). |   |   |   |   |   |
| F2 | Message success/error feedback was clear. |   |   |   |   |   |
| F3 | I could find and view my messages/conversations. |   |   |   |   |   |

Notes:

---

## G. Overall Usability

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| G1 | The interface looks consistent and professional. |   |   |   |   |   |
| G2 | The layout is responsive on desktop and mobile widths. |   |   |   |   |   |
| G3 | The system is easy to navigate overall. |   |   |   |   |   |
| G4 | Errors I triggered were understandable and recoverable. |   |   |   |   |   |

Notes:

---

## H. Summary

| Metric | Value |
|--------|-------|
| Total statements rated |       |
| Average score (1–5)   |       |
| % rated 4 or 5        |       |
| Key strengths          |       |
| Suggested improvements |       |
| Acceptance decision (Accept / Accept with changes / Reject) | |

---

_Signature / Date: _______________________

_This form is part of the Sprint 7.5 user-acceptance/usability evidence. All
entries must come from real use of the running application (AGENTS 39, 40)._
