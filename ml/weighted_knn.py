"""
Feature weighting and weighted Euclidean distance (Phase 5, Sprint 5.4).

This module is the **weighted-distance engine** deliverable of Sprint 5.4: it
resolves the feature weights configured for the system and computes the
weighted Euclidean distance between a tenant query vector ``U`` and an
apartment candidate vector ``A`` (AGENTS 12, 14):

    Dw(U,A) = sqrt( Σi wi·(ui − ai)² )

Smaller distance means greater similarity, so candidates are later ranked by
ascending distance (Sprint 5.5).

Design notes:

- Weights resolve from the Sprint 5.1 defaults (``ml.features``) or a
  validated override, so the engine works with the default configuration out
  of the box and stays configurable.
- The categorical ``apartment_type`` feature is one-hot encoded (Sprint 5.2).
  Its base weight is applied to whichever column is active: when the tenant
  stated a type, the single set column contributes to the distance; when a
  tenant stated no type preference, no column contributes.
- Unstated (missing) tenant preferences are neutralised at weighting time via
  the ``active`` mask produced by ``ml.preprocessing``: a dimension whose
  tenant value is ``None`` or whose mask entry is False contributes nothing,
  so an out-of-scope dimension never inflates the distance.

This engine computes a single pair distance only; candidate selection, hard
filtering and K-selection/ranking are Sprint 5.5.
"""
import math

from ml.features import DEFAULT_FEATURE_WEIGHTS, validate_feature_weights
from ml.preprocessing import ONE_HOT_SEPARATOR

CATEGORICAL_BASE = "apartment_type"


def _base_weight_name(name):
    """Map an encoded dimension back to its base feature name.

    One-hot columns ``apartment_type_<X>`` resolve to the base weight for
    ``apartment_type``; every other encoded dimension uses its own weight key.
    """
    if name.startswith(CATEGORICAL_BASE + ONE_HOT_SEPARATOR):
        return CATEGORICAL_BASE
    return name


def resolve_weights(weights=None):
    """Resolve the effective feature-weight mapping.

    ``None`` returns a copy of the Sprint 5.1 defaults. Any supplied mapping
    is validated (must cover every feature with non-negative values) and, if
    valid, used as the effective weights.
    """
    if weights is None:
        return dict(DEFAULT_FEATURE_WEIGHTS)
    if not validate_feature_weights(weights):
        raise ValueError(
            "Feature weights must cover every feature with non-negative "
            "numerical values."
        )
    return dict(weights)


def _weight_for(name, weights):
    """Return the base weight for an encoded dimension."""
    return weights.get(_base_weight_name(name), 0.0)


def weighted_distance(
    tenant_vector,
    apartment_vector,
    active_mask=None,
    weights=None,
):
    """Compute the weighted Euclidean distance between a tenant query and an
    apartment candidate.

    ``tenant_vector`` and ``apartment_vector`` are encoded vectors as produced
    by ``ml.preprocessing`` (Sprint 5.2/5.3). ``active_mask`` marks the
    dimensions on which the tenant expressed a preference; any dimension whose
    tenant value is ``None`` or whose mask entry is False is neutralised
    (weight 0). Returns a non-negative float; identical vectors give 0.0.
    """
    effective = resolve_weights(weights)
    total = 0.0
    for name, ui in tenant_vector.items():
        if ui is None:
            continue
        if active_mask is not None and not active_mask.get(name, False):
            continue
        weight = _weight_for(name, effective)
        if weight <= 0:
            continue
        aj = apartment_vector.get(name)
        if aj is None:
            continue
        diff = ui - aj
        total += weight * diff * diff
    return math.sqrt(total)


def similarity(tenant_vector, apartment_vector, active_mask=None, weights=None):
    """Return a bounded "preference match" similarity score from a distance.

    Uses an exponential decay (``e ** (-distance)``) so a perfect match
    (distance 0) yields 1.0 and larger distances approach 0.0. This is an
    interpretive convenience for display ("similarity score") and is derived
    strictly from the computed weighted distance (AGENTS 17, 43).
    """
    distance = weighted_distance(
        tenant_vector,
        apartment_vector,
        active_mask=active_mask,
        weights=weights,
    )
    return math.exp(-distance)
