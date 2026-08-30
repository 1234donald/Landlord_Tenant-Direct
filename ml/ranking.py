"""
Weighted KNN candidate selection and ranking (Phase 5, Sprint 5.5).

This module is the **Weighted KNN ranking engine** deliverable of Sprint 5.5.
It retrieves the eligible apartments for a tenant, applies the Sprint 5.1 hard
filters, computes each candidate's weighted distance (Sprint 5.4), sorts the
candidates by ascending distance (smallest distance = greatest relevance,
AGENTS 12), selects the K nearest, and assigns 1-based ranking positions.

It composes the earlier Phase 5 building blocks:

- ``ml.preprocessing``: apartment/tenant vector construction, one-hot/binary
  encoding, and min-max normalisation against the candidate set;
- ``ml.weighted_knn``: the weighted Euclidean distance;
- ``ml.features``: hard-filter fields, binary features and the default K.

Hard filters are applied *before* similarity ranking (AGENTS 15); only eligible
candidates are considered, so an apartment that violates a mandatory constraint
(e.g. price cap) is never recommended merely for similarity. When there are
fewer eligible candidates than K, all eligible candidates are returned (still
ranked); ties are broken stably by input order.
"""
from math import exp

from ml.features import BINARY_FEATURES, DEFAULT_K
from ml.preprocessing import (
    encode_apartment_vector,
    encode_tenant_vector,
    feature_bounds,
    normalise_features,
    normalise_tenant_vector,
)
from ml.weighted_knn import weighted_distance


def hard_filter_queryset(queryset, preference):
    """Apply the Sprint 5.1 hard filters to an apartment queryset.

    Uses a tenant's stored ``Preference`` to restrict candidates to those that
    satisfy every mandatory constraint (AGENTS 15):

    - availability is always required;
    - a preferred location must appear (case-insensitive) in the apartment
      location;
    - ``rental_price <= max_rent`` (price cap);
    - an exact ``apartment_type`` when stated;
    - bedrooms and bathrooms must be at least the preferred minimums;
    - a facility that is *required* (True) must be provided.

    ``False`` or ``None`` facility preferences impose no constraint. The
    returned queryset is still lazy; nothing is evaluated here.
    """
    qs = queryset.filter(availability=True)

    location = preference.location
    if location:
        qs = qs.filter(location__icontains=location.strip())

    if preference.max_rent is not None:
        qs = qs.filter(rental_price__lte=preference.max_rent)

    if preference.apartment_type:
        qs = qs.filter(apartment_type=preference.apartment_type)

    if preference.bedrooms is not None:
        qs = qs.filter(bedrooms__gte=preference.bedrooms)

    if preference.bathrooms is not None:
        qs = qs.filter(bathrooms__gte=preference.bathrooms)

    for field in BINARY_FEATURES:
        if getattr(preference, field) is True:
            qs = qs.filter(**{field: True})

    return qs


def rank_recommendations(apartments, preference, k=None, weights=None):
    """Rank an iterable of eligible ``Apartment`` objects by similarity.

    ``apartments`` must already be hard-filtered (or callers may build a list
    of arbitrary apartments to compare). Returns a list of result dicts ordered
    by ascending distance:

        {"apartment": <Apartment>, "rank": 1..K, "distance": float,
         "similarity": float}

    ``k`` defaults to the configurable ``DEFAULT_K``; when fewer than ``k``
    candidates are eligible, all of them are returned (ranked). ``weights`` is
    an optional validated weight override for the distance engine.
    """
    neighbour_count = DEFAULT_K if k is None else k
    candidates = list(apartments)
    if not candidates:
        return []

    tenant_vector, active_mask = encode_tenant_vector(preference)
    encoded = [(apt, encode_apartment_vector(apt)) for apt in candidates]

    bounds = feature_bounds([vector for _, vector in encoded])
    normalised = [
        (apt, normalise_features(vector, bounds)) for apt, vector in encoded
    ]
    normalised_tenant = normalise_tenant_vector(tenant_vector, bounds)

    scored = []
    for apt, vector in normalised:
        distance = weighted_distance(
            normalised_tenant,
            vector,
            active_mask=active_mask,
            weights=weights,
        )
        scored.append((distance, apt))
    scored.sort(key=lambda pair: pair[0])

    results = []
    for rank, (distance, apt) in enumerate(scored[:neighbour_count], start=1):
        results.append(
            {
                "apartment": apt,
                "rank": rank,
                "distance": float(distance),
                "similarity": float(exp(-distance)),
            }
        )
    return results


def recommend(queryset, preference, k=None, weights=None):
    """Recommend apartments from a base queryset for a tenant preference.

    Applies the hard filters, then ranks the eligible candidates. This is the
    primary entry point for the recommendation engine (used by the Sprint 5.6
    service/API layer).
    """
    eligible = hard_filter_queryset(queryset, preference)
    return rank_recommendations(eligible, preference, k=k, weights=weights)
