# Weighted KNN Recommendation — Feature Specification

**Phase 5 (Recommendation), Sprint 5.1 — Deliverable**

This document is the **recommendation feature specification** for the platform's
intelligent apartment recommendation component. It is the source of truth for
what is fed into the Weighted KNN algorithm and is mirrored by the authoritative
constants in `ml/features.py`.

The feature set below is **confirmed** and maps **one-to-one to the database
schema** (`apps.apartments.models.Apartment` and
`apps.recommendations.models.Preference`), so no ML feature is created that
cannot be obtained from the real system (AGENTS 13, 41).

---

## 1. Confirmed feature list

Nine distance features participate in the Weighted KNN similarity computation:

| # | Feature          | Kind        | Apartment source       | Preference source |
|---|------------------|-------------|------------------------|-------------------|
| 1 | `rental_price`   | Numerical   | `Apartment.rental_price` | `Preference.max_rent` |
| 2 | `bedrooms`       | Numerical   | `Apartment.bedrooms`   | `Preference.bedrooms` |
| 3 | `bathrooms`      | Numerical   | `Apartment.bathrooms`  | `Preference.bathrooms` |
| 4 | `apartment_type` | Categorical | `Apartment.apartment_type` | `Preference.apartment_type` |
| 5 | `parking`        | Binary      | `Apartment.parking`    | `Preference.parking` |
| 6 | `electricity`    | Binary      | `Apartment.electricity`| `Preference.electricity` |
| 7 | `water`          | Binary      | `Apartment.water`      | `Preference.water` |
| 8 | `security`       | Binary      | `Apartment.security`   | `Preference.security` |
| 9 | `furnished`      | Binary      | `Apartment.furnished`  | `Preference.furnished` |

**Location** (`location`) is not a weighted distance term; it is an *eligibility*
(hard-filter) criterion because it is free text. The same applies to
`availability` (always required) and `address`.

---

## 2. Feature classification

- **Numerical (normalised min–max):** `rental_price`, `bedrooms`, `bathrooms`.
  Normalised with `x' = (x − xmin) / (xmax − xmin)`; the implementation guards
  against division-by-zero when min == max (AGENTS 14).
- **Categorical (one-hot encoded):** `apartment_type` with labels
  `SELF_CONTAINED, ONE_BEDROOM, TWO_BEDROOM, THREE_BEDROOM, FLAT, DUPLEX`.
- **Binary (0 / 1):** `parking`, `electricity`, `water`, `security`, `furnished`.

---

## 3. Feature weights (configurable)

Weights are non-negative and applied inside the weighted Euclidean distance

```
Dw(U,A) = sqrt( Σi wi(ui − ai)² )
```

Smaller distance ⇒ greater relevance. Defaults (overridable via application
settings, validated by `ml.features.validate_feature_weights`):

| Feature          | Default weight |
|------------------|----------------|
| `rental_price`   | 3.0            |
| `bedrooms`       | 2.0            |
| `bathrooms`      | 2.0            |
| `apartment_type` | 2.0            |
| `parking`        | 1.0            |
| `electricity`    | 1.0            |
| `water`          | 1.0            |
| `security`       | 1.0            |
| `furnished`      | 1.0            |
| `location` (hard) | 2.0          |

`rental_price` is weighted highest because it is the most decisive factor for a
prospective tenant; unit size and type come next; facility flags are lighter
tie-breakers.

---

## 4. Hard filters (applied BEFORE similarity ranking)

A candidate apartment must satisfy every rule to be eligible; Weighted KNN then
ranks only the eligible candidates (AGENTS 15):

1. **Availability** — `availability is True` (always).
2. **Location** — the tenant's preferred `location` must be a case-insensitive
   substring of the apartment's `location`.
3. **Price cap** — if `Preference.max_rent` is set,
   `Apartment.rental_price <= Preference.max_rent`.
4. **Apartment type** — if `Preference.apartment_type` is set, it must equal
   `Apartment.apartment_type`.
5. **Unit size** — if set, `bedrooms` and `bathrooms` must be `>=` the preferred
   minimums.
6. **Facilities** — if a facility (`parking`, `electricity`, `water`,
   `security`, `furnished`) is required (True), the apartment must provide it.

These mirror the existing search/filter logic in
`apps.apartments.views.build_search_queryset` so hard filtering is consistent
across search and recommendation.

---

## 5. Query and candidate vectors

- **Query vector U** is built from the tenant's stored `Preference`, applying
  encoding and missing-value handling for unstated preferences.
- **Candidate vector A** is built from each eligible `Apartment`.
- **K** is configurable (`DEFAULT_K = 5`), selected and evaluated during
  testing (AGENTS 16).

## 6. Claims

The recommendations are similarity-based and derived from available structured
data and stated tenant preferences. The system does **not** claim guaranteed
bests, human-level intelligence, or fraud-proof listings (AGENTS 17).
