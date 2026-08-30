"""Service layer for the Recommendation module (Phases 4-5).

This module keeps business logic out of views and templates (AGENTS 6).

- ``prepare_preference_data`` (Sprint 4.4) prepares a tenant's stored preference
  as the structured query information consumed by the Weighted KNN component.
- ``generate_recommendations`` (Sprint 5.6) is the recommendation service layer:
  it runs the Weighted KNN engine over the candidate apartments, persists the
  resulting ``Recommendation`` / ``RecommendationItem`` records, and raises clear
  exceptions the API layer turns into user-facing errors.
"""
from apps.apartments.models import Apartment
from ml.features import DEFAULT_K
from ml.ranking import recommend as run_ranking_engine

from .models import Preference, Recommendation, RecommendationItem


def _as_str(value):
    """Render a field value as the recommended service's preferred string form.

    ``None`` is preserved so an unstated preference ("no preference") is kept
    distinct from an explicit value when the recommendation component applies
    hard filters and encodes categorical values (AGENTS 15).
    """
    if value is None:
        return None
    return str(value)


def prepare_preference_data(preference):
    """Prepare a stored ``Preference`` as recommendation-ready query data.

    Returns a plain dict capturing every preference attribute in a canonical
    shape (decimal prices as ``str``, apartment type as the raw choice value,
    booleans as ``True``/``False``, and ``None`` kept for unstated values). The
    raw choice value for ``apartment_type`` is preserved so the recommendation
    component can apply its chosen categorical encoding without an imposed
    ordinal mapping (SYSTEM_REQUIREMENTS 13).

    This payload is the deterministic, testable bridge between the persisted
    preference and the Phase 5 Weighted KNN feature pipeline. It performs no
    similarity calculation.
    """
    return {
        "tenant_id": preference.tenant_id,
        "location": preference.location or None,
        "max_rent": _as_str(preference.max_rent),
        "apartment_type": preference.apartment_type,
        "bedrooms": preference.bedrooms,
        "bathrooms": preference.bathrooms,
        "parking": preference.parking,
        "electricity": preference.electricity,
        "water": preference.water,
        "security": preference.security,
        "furnished": preference.furnished,
        "additional_facilities": preference.additional_facilities or None,
    }


def apartment_type_labels():
    """Return the supported apartment-type choices for preference forms/UI.

    Delegates to the ``Apartment`` model so the preference module always stays
    consistent with the listing schema (AGENTS 13).
    """
    return Apartment.ApartmentType.choices


class NoPreferenceError(Exception):
    """Raised when a tenant has no stored preference to recommend from."""


def generate_recommendations(tenant, preference):
    """Run the Weighted KNN engine for a tenant's preference and persist the run.

    Returns the created ``Recommendation`` (with its ``items``). The engine
    applies hard filters and ranks the eligible apartments (``ml.ranking``);
    every ranked candidate is persisted as a ``RecommendationItem`` with its
    1-based rank, weighted distance and similarity. When nothing is eligible,
    a ``Recommendation`` with no items is still returned so the flow is
    observable and the API can communicate the empty result gracefully.
    """
    if preference is None:
        raise NoPreferenceError(
            "Save an apartment preference first so we can personalise "
            "recommendations."
        )
    if preference.tenant_id != tenant.id:
        raise NoPreferenceError("The preference does not belong to this tenant.")

    results = run_ranking_engine(Apartment.objects.all(), preference)

    recommendation = Recommendation.objects.create(
        tenant=tenant,
        preference=preference,
        algorithm=Recommendation.Algorithm.WEIGHTED_KNN,
        k=DEFAULT_K,
    )
    RecommendationItem.objects.bulk_create(
        [
            RecommendationItem(
                recommendation=recommendation,
                apartment=result["apartment"],
                rank=result["rank"],
                distance=result["distance"],
                similarity=result["similarity"],
            )
            for result in results
        ]
    )
    return recommendation
