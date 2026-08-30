"""
Feature extraction and encoding for Weighted KNN (Phase 5, Sprint 5.2).

This module implements the **feature-processing pipeline** deliverable of
Sprint 5.2: tenant-vector construction, apartment-vector construction,
categorical encoding, binary feature encoding and missing-value handling.

It consumes the authoritative feature specification in ``ml.features``
(Sprint 5.1) and produces encoded integer/float dictionaries that are later
consumed by normalisation (Sprint 5.3) and the weighted distance (Sprint 5.4).

Scope notes:

- Numerical features are emitted as *raw* values; min-max normalisation is a
  separate Sprint 5.3 responsibility (AGENTS 14).
- Categorical (apartment type) features are one-hot encoded (AGENTS 14).
- Binary facility features are encoded as 0/1.
- Missing (unstated) tenant preferences are preserved as ``None`` together
  with an ``active`` mask so later steps can neutralise the contribution of
  unstated dimensions (a preference model may legitimately be ``None``).
- No similarity calculation is performed here (Sprint 5.4).
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
