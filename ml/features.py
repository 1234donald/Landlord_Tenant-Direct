"""
Weighted KNN recommendation - feature specification (Phase 5, Sprint 5.1).

This module is the authoritative *feature specification* for the Weighted KNN
recommendation component (AGENTS 11-16, 27). It is produced in Sprint 5.1 and
defines, once, the single source of truth that later sprints consume:

- the confirmed feature list;
- the mapping from database fields to ML features;
- the classification (numerical / categorical / binary) of each feature;
- the hard filters applied before similarity ranking;
- the configurable feature weights.

The final feature set below corresponds exactly to the database schema
(``apps.apartments.models.Apartment`` and
``apps.recommendations.models.Preference``) so no ML feature is created that
cannot be obtained from the actual system (AGENTS 13, 41).

IMPORTANT - Soft-consistency rule:

Weights may be tuned for the recommendation quality evaluation (Sprint 5.x).
Every other value in this module reflects a deployed project decision and must
remain consistent with both the database schema and the existing hard-filter
logic in ``apps.apartments.views.build_search_queryset``.

Hard filters are applied before similarity ranking (AGENTS 15). Weighted KNN
ranks only the eligible candidate apartments.
"""

# ---------------------------------------------------------------------------
# Feature list
# ---------------------------------------------------------------------------
# Every distance-computable feature used to build the apartment candidate
# vector A and the tenant preference query vector U (AGENTS 12). The set was
# confirmed from SYSTEM_REQUIREMENTS §39 (Sprint 5.1) and maps one-to-one to
# the database schema.

# Signals the endpoints later used by feature extraction to separate purely
# categorical (one-hot encoded) features from numerical binary features.
FEATURE_NAMES = (
    "rental_price",
    "bedrooms",
    "bathrooms",
    "apartment_type",
    "parking",
    "electricity",
    "water",
    "security",
    "furnished",
)

# ---------------------------------------------------------------------------
# Number of nearest neighbours (K)
# ---------------------------------------------------------------------------
# K is configurable (AGENTS 16). A sensible default of 5 is used and evaluated
# during testing; production can override it through application settings by
# importing this constant.
DEFAULT_K = 5


# ---------------------------------------------------------------------------
# Feature classification
# ---------------------------------------------------------------------------
NUMERICAL_FEATURES = (
    "rental_price",
    "bedrooms",
    "bathrooms",
)

CATEGORICAL_FEATURES = (
    "apartment_type",
)

BINARY_FEATURES = (
    "parking",
    "electricity",
    "water",
    "security",
    "furnished",
)

# Valid categorical labels for one-hot encoding (mirrors Apartment.ApartmentType).
APARTMENT_TYPES = (
    "SELF_CONTAINED",
    "ONE_BEDROOM",
    "TWO_BEDROOM",
    "THREE_BEDROOM",
    "FLAT",
    "DUPLEX",
)


# ---------------------------------------------------------------------------
# Database field mapping
# ---------------------------------------------------------------------------
# Maps each distance feature to the field on the Apartment (candidate) side
# and the field on the Preference (query) side. `None` means that side does
# not directly provide the feature (it is derived/encoded separately).
APARTMENT_FIELD_MAP = {
    "rental_price": "rental_price",
    "bedrooms": "bedrooms",
    "bathrooms": "bathrooms",
    "apartment_type": "apartment_type",
    "parking": "parking",
    "electricity": "electricity",
    "water": "water",
    "security": "security",
    "furnished": "furnished",
}

PREFERENCE_FIELD_MAP = {
    "rental_price": "max_rent",
    "bedrooms": "bedrooms",
    "bathrooms": "bathrooms",
    "apartment_type": "apartment_type",
    "parking": "parking",
    "electricity": "electricity",
    "water": "water",
    "security": "security",
    "furnished": "furnished",
}


# ---------------------------------------------------------------------------
# Hard filters (applied BEFORE similarity ranking)
# ---------------------------------------------------------------------------
# A preference is only eligible for ranking when it passes every hard filter.
# The price and facility rules mirror build_search_queryset; availability and
# location are always applied so an unavailable or out-of-area apartment is
# never recommended merely because it looks similar (AGENTS 15, 41).
HARD_FILTER_AVAILABILITY = True

# Location is treated as an eligibility criterion (case-insensitive substring
# match) rather than a weighted numeric feature because it is free text.
LOCATION_FILTER_ENABLED = True

# Fields on Preference (query side) whose presence triggers an exact / minimum
# hard constraint on the matching Apartment field.
HARD_FILTER_FIELDS = (
    "max_rent",
    "apartment_type",
    "bedrooms",
    "bathrooms",
    "parking",
    "electricity",
    "water",
    "security",
    "furnished",
)


# ---------------------------------------------------------------------------
# Feature weights
# ---------------------------------------------------------------------------
# Configurable, non-negative weights applied within the weighted Euclidean
# distance (AGENTS 12, 14). Larger weights make a feature contribute more to
# similarity. Defaults prioritise price and unit size, then apartment type,
# then the facility flags.
DEFAULT_FEATURE_WEIGHTS = {
    "rental_price": 3.0,
    "bedrooms": 2.0,
    "bathrooms": 2.0,
    "apartment_type": 2.0,
    "parking": 1.0,
    "electricity": 1.0,
    "water": 1.0,
    "security": 1.0,
    "furnished": 1.0,
}

# Weight of the 'location' eligibility criterion relative to the other
# features. Kept separate because location operates as a hard filter rather
# than a numeric distance term.
LOCATION_WEIGHT = 2.0


def validate_feature_weights(weights):
    """Return True when ``weights`` is a valid override for the defaults.

    A valid weight mapping covers exactly the feature set with non-negative
    values. Raising a clear error at configuration time avoids silent ranking
    errors later.
    """
    if not isinstance(weights, dict):
        return False
    for name in FEATURE_NAMES:
        value = weights.get(name)
        if value is None or not isinstance(value, (int, float)):
            return False
        if value < 0:
            return False
    return True
