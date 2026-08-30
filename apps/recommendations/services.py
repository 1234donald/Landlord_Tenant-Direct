"""Service layer for the Tenant Preference module (Phase 4, Sprint 4.4).

This module keeps business logic out of views and templates (AGENTS 6). Its
purpose here is to prepare a tenant's stored preference as the structured query
information that the Weighted KNN recommendation component (Phase 5) will
consume.

It deliberately does NOT implement the recommendation algorithm. Feature
extraction, categorical encoding, normalisation, weighting and distance
calculation are all Phase 5 (Sprint 5.x) responsibilities. This service only
produces the preference payload, in a stable and testable shape, that the next
phase will turn into the query vector ``U = (u1, ..., un)`` (AGENTS 12).
"""
from decimal import Decimal

from apps.apartments.models import Apartment


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
