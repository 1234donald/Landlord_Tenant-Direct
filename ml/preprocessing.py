"""
Feature extraction, encoding and numerical normalisation for Weighted KNN
(Phase 5, Sprints 5.2 and 5.3).

This module implements the feature-processing pipeline (Sprint 5.2) and the
numerical normalisation service (Sprint 5.3):

- tenant-vector construction, apartment-vector construction;
- categorical (one-hot) encoding and binary 0/1 encoding;
- missing-value handling (``None`` plus an ``active`` mask);
- min-max normalisation of numerical features with division-by-zero
  protection (AGENTS 14).

It consumes the authoritative feature specification in ``ml.features``
(Sprint 5.1) and produces encoded, normalised numeric dictionaries that are
later consumed by the weighted distance (Sprint 5.4). Categorical and binary
features are emitted as 0/1 and are not rescaled by normalisation; only the
numerical features are min-max normalised. No similarity calculation is
performed here (Sprint 5.4).
"""
from apps.apartments.models import Apartment

from ml.features import (
    APARTMENT_FIELD_MAP,
    APARTMENT_TYPES,
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_NAMES,
    NUMERICAL_FEATURES,
    PREFERENCE_FIELD_MAP,
)

ONE_HOT_SEPARATOR = "_"


def one_hot_columns():
    """Return the ordered one-hot column names for ``apartment_type``.

    Produces ``apartment_type_SELF_CONTAINED`` ... ``apartment_type_DUPLEX``.
    """
    return tuple(f"apartment_type{ONE_HOT_SEPARATOR}{label}" for label in APARTMENT_TYPES)


def encode_binary(value):
    """Encode a boolean facility flag as 0/1, preserving ``None`` (unstated)."""
    if value is None:
        return None
    return 1 if value else 0


def one_hot_encode_apartment_type(value):
    """One-hot encode an apartment-type value into a dict of 0/1 columns.

    ``None`` (no type stated) produces all-zero columns with no active bit.
    """
    if value is None:
        return {column: 0 for column in one_hot_columns()}
    return {column: (1 if column.endswith(ONE_HOT_SEPARATOR + value) else 0)
            for column in one_hot_columns()}


def apartment_feature_vector(apartment):
    """Extract the raw feature values from an ``Apartment`` model instance.

    Returns a dict keyed by the distance feature names; numerical values are
    raw, the categorical value is the raw choice string, and binary facility
    flags are raw booleans (always present on an apartment).
    """
    vector = {}
    for name in FEATURE_NAMES:
        field = APARTMENT_FIELD_MAP[name]
        value = getattr(apartment, field)
        if name in NUMERICAL_FEATURES and value is not None:
            value = float(value)
        vector[name] = value
    return vector


def preference_feature_vector(preference):
    """Extract the raw feature values from a ``Preference`` model instance.

    Unstated preferences (nullable fields) are returned as ``None`` so missing
    values can be handled explicitly by encoding and later weighting. Numerical
    values are coerced to ``float`` when present.
    """
    vector = {}
    for name in FEATURE_NAMES:
        field = PREFERENCE_FIELD_MAP[name]
        value = getattr(preference, field)
        if name in NUMERICAL_FEATURES and value is not None:
            value = float(value)
        vector[name] = value
    return vector


def encode_apartment_vector(apartment):
    """Build the full encoded numeric vector ``A`` for an apartment.

    Numerical features are emitted raw, the categorical type is expanded into
    its one-hot columns, and binary facilities are 0/1. The apartment side is
    fully populated so no mask is required.
    """
    raw = apartment_feature_vector(apartment)
    vector = {}

    for name in NUMERICAL_FEATURES:
        vector[name] = raw[name]

    for name in CATEGORICAL_FEATURES:
        vector.update(one_hot_encode_apartment_type(raw[name]))

    for name in BINARY_FEATURES:
        vector[name] = encode_binary(raw[name])

    return vector


def encode_tenant_vector(preference):
    """Build the encoded query vector ``U`` and its active mask.

    Returns ``(vector, active_mask)`` where each is a dict keyed by encoded
    feature name. ``active_mask[name]`` is True only when the tenant has
    stated a preference for that dimension (numeric present, type stated, or a
    facility set to True/False); unstated dimensions (None) yield an inactive
    slot so later weighting can neutralise them.
    """
    raw = preference_feature_vector(preference)
    vector = {}
    active_mask = {}

    for name in NUMERICAL_FEATURES:
        value = raw[name]
        vector[name] = None if value is None else float(value)
        active_mask[name] = value is not None

    type_value = raw[CATEGORICAL_FEATURES[0]]
    for column in one_hot_columns():
        vector[column] = 1 if type_value and column.endswith(ONE_HOT_SEPARATOR + type_value) else 0
        active_mask[column] = type_value is not None and column.endswith(
            ONE_HOT_SEPARATOR + type_value
        )

    for name in BINARY_FEATURES:
        value = raw[name]
        vector[name] = None if value is None else (1 if value else 0)
        active_mask[name] = value is not None

    return vector, active_mask


def validate_encoded_pair(apartment_vector, tenant_vector, active_mask):
    """Return True when the encoded vectors share a consistent shape.

    Guards against a drift between the apartment and tenant encodings (e.g. a
    tenant vector that does not cover a one-hot column) before any distance is
    computed.
    """
    if set(tenant_vector) != set(apartment_vector):
        return False
    if set(active_mask) != set(tenant_vector):
        return False
    return True


# ---------------------------------------------------------------------------
# Numerical normalisation (Sprint 5.3)
# ---------------------------------------------------------------------------
def feature_bounds(encoded_apartment_vectors):
    """Compute ``(min, max)`` for each numerical feature across the apartments.

    ``encoded_apartment_vectors`` is an iterable of encoded apartment vectors
    (as produced by ``encode_apartment_vector``). Only the numerical feature
    dimensions are considered. When there are no values for a feature the
    bound is ``(0.0, 0.0)`` so normalisation stays well-defined.
    """
    values = {name: [] for name in NUMERICAL_FEATURES}
    for vector in encoded_apartment_vectors:
        for name in NUMERICAL_FEATURES:
            value = vector.get(name)
            if value is not None:
                values[name].append(float(value))

    bounds = {}
    for name in NUMERICAL_FEATURES:
        if values[name]:
            bounds[name] = (min(values[name]), max(values[name]))
        else:
            bounds[name] = (0.0, 0.0)
    return bounds


def min_max_normalise(value, lower, upper):
    """Min-max normalise a single value into ``[0, 1]`` (x' = (x-min)/(max-min)).

    ``None`` (a missing/unstated preferference) is passed through unchanged.
    When ``lower == upper`` the feature is constant over the candidate set and
    the range is zero; division by zero is avoided by returning ``0.0`` so the
    feature contributes nothing to discrimination (AGENTS 14, 27).
    """
    if value is None:
        return None
    span = upper - lower
    if span == 0:
        return 0.0
    return (float(value) - lower) / span


def normalise_features(vector, bounds):
    """Return a copy of an encoded vector with numerical features normalised.

    Numerical feature dimensions are rescaled with ``bounds``; categorical
    (one-hot) and binary dimensions are copied through unchanged. Missing
    values (``None``) are preserved.
    """
    out = dict(vector)
    for name in NUMERICAL_FEATURES:
        if name not in out:
            continue
        lower, upper = bounds[name]
        out[name] = min_max_normalise(out[name], lower, upper)
    return out


def normalise_apartments(encoded_apartment_vectors):
    """Normalise a collection of encoded apartment vectors against their own range.

    Returns ``(bounds, normalised_vectors)`` where ``bounds`` is the per-feature
    ``(min, max)`` computed across the collection and each vector is normalised
    with those same bounds, so rankings are reproducible for the candidate set.
    """
    bounds = feature_bounds(encoded_apartment_vectors)
    return bounds, [normalise_features(vector, bounds) for vector in encoded_apartment_vectors]


def normalise_tenant_vector(encoded_tenant_vector, bounds):
    """Normalise the numerical features of an encoded tenant query vector.

    ``bounds`` must match those used to normalise the candidate apartments so
    the query vector ``U`` and candidate vectors ``A`` share a common frame.
    """
    return normalise_features(encoded_tenant_vector, bounds)
