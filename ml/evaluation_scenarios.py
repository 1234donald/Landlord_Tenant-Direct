"""
Reproducible evaluation scenarios (Phase 5, Sprint 5.7).

Sprint 5.7 task "create reproducible test scenarios" and "prepare evaluation
dataset/test cases". This module provides a small library of **deterministic**
scenarios used to validate the recommendation metrics (``ml.evaluation``) and
to document expected known-value results. Everything here is explicitly
**test / evaluation data** (AGENTS 40): it is synthetic, clearly labelled, and
never presented as real-world data. Every helper produces the same output on
every call, so the metrics and ranking behaviour are fully reproducible.

The metric scenarios feed ``ml.evaluation`` directly; the apartment scenario is
a small, controlled catalogue of features that the Django-based validation test
uses with the real ``ml.ranking`` engine against actual apartment records.
"""
import math

# ---------------------------------------------------------------------------
# Metric evaluation scenarios (known expected values)
# ---------------------------------------------------------------------------


def _ranking(identities):
    """Build the result-dict shape used by ``ml.ranking`` from plain identities.

    Distances are arbitrary descending-magnitude placeholders (``9 - position``)
    purely so the result dicts mirror the engine shape; they do not affect the
    rank-matching metrics, which only read the ordered identities.
    """
    return [
        {"apartment": apartment_id, "distance": float(9 - position)}
        for position, apartment_id in enumerate(identities, start=1)
    ]


def metric_scenario_simple():
    """Three relevant apartments; the top five contain two of them.

    Relevant       = {2, 5, 9}
    Retrieved (top-5) = [1, 2, 3, 4, 5]  -> hits at rank 2 and rank 5.

    Expected (k=5):
        precision = 2/5 = 0.4
        recall    = 2/3  ~ 0.6667
        hit_rate  = 1.0
        ndcg      = (1/log2(3) + 1/log2(6)) / (1/log2(2) + 1/log2(3) + 1/log2(4))
    """
    ranking = _ranking([1, 2, 3, 4, 5])
    relevant = {2, 5, 9}
    k = 5
    expected = {
        "precision": 2 / 5,
        "recall": 2 / 3,
        "hit_rate": 1.0,
        "ndcg": (
            (1.0 / math.log2(3)) + (1.0 / math.log2(6))
        )
        / (
            1.0 / math.log2(2)
            + 1.0 / math.log2(3)
            + 1.0 / math.log2(4)
        ),
    }
    return ranking, relevant, k, expected


def metric_scenario_no_hit():
    """No retrieved apartment is relevant -> all metrics are 0."""
    ranking = _ranking([10, 11, 12])
    relevant = {99}
    k = 2
    return ranking, relevant, k, {
        "precision": 0.0,
        "recall": 0.0,
        "hit_rate": 0.0,
        "ndcg": 0.0,
    }


def metric_scenario_empty_relevant():
    """An empty relevance set -> recall/hit/ndcg 0; precision 0 (no relevant hits)."""
    ranking = _ranking([1, 2, 3])
    relevant = set()
    k = 2
    return ranking, relevant, k, {
        "precision": 0.0,
        "recall": 0.0,
        "hit_rate": 0.0,
        "ndcg": 0.0,
    }


def metric_scenario_k_larger_than_retrieved():
    """K exceeds the number of retrieved results -> scored over what exists."""
    ranking = _ranking([1, 2])
    relevant = {1}
    k = 5
    return ranking, relevant, k, {
        "precision": 0.5,  # 1 hit / 2 retrieved
        "recall": 1.0,
        "hit_rate": 1.0,
        "ndcg": 1.0,
    }


def metric_scenario_perfect_ranking():
    """All relevant apartments are the retrieved top-K -> all metrics 1.0."""
    ranking = _ranking([7, 8, 9])
    relevant = {7, 8, 9}
    k = 3
    return ranking, relevant, k, {
        "precision": 1.0,
        "recall": 1.0,
        "hit_rate": 1.0,
        "ndcg": 1.0,
    }


# ---------------------------------------------------------------------------
# Controlled apartment-feature scenario (for the real ranking engine)
# ---------------------------------------------------------------------------


def controlled_apartment_catalogue():
    """A deterministic mini-catalogue of apartment features + ground truth.

    Returns a dict with two keys:

    - ``candidates``: ordered list of apartment dicts giving the feature values
      used to create real ``Apartment`` records in a validation test. Feature
      keys match the ``Apartment`` fields used by the recommendation pipeline.
    - ``relevant``: the identities (ranks in the candidate order, 1-based) that
      a rational "tenant who wants a 2-bed, 2-bath, furnished, secured flat in
      Calabar under N300k" would consider relevant.

    This is explicitly synthetic evaluation data for testing only (AGENTS 40).
    """
    candidates = [
        dict(title="Calabar 2bd furnished secured", location="Calabar",
             rental_price="180000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True),
        dict(title="Calabar 2bd unfurnished", location="Calabar",
             rental_price="250000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=False),
        dict(title="Calabar 3bd expensive", location="Calabar",
             rental_price="450000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=True),
        dict(title="Overseas studio", location="Uyo",
             rental_price="120000.00", apartment_type="SELF_CONTAINED",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False),
        dict(title="Calabar 1bd too small", location="Calabar",
             rental_price="150000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False),
    ]
    # Identity is the 1-based position in the catalogue above.
    relevant = {1, 2}
    return {"candidates": candidates, "relevant": relevant}


# ---------------------------------------------------------------------------
# Formal evaluation catalogue (deterministic, multi-location evaluation data)
#
# The 5-apartment ``controlled_apartment_catalogue`` above is the compact unit
# fixture: it has at most 5 eligible candidates, so a K=3/5/7 comparison is not
# always meaningful there. The formal evaluation of Chapter Four therefore adds
# a larger, deterministic catalogue. It is the SAME kind of clearly-labelled
# synthetic test/evaluation data (AGENTS 40), never presented as real-world
# data, and it is only used to run the real engine against real records.
# ---------------------------------------------------------------------------

FACILITY_FEATURES = ("parking", "electricity", "water", "security", "furnished")


def formal_evaluation_catalogue():
    """A 32-apartment deterministic catalogue for the formal Chapter Four eval.

    Indices 1-5 are exactly the same apartments as
    ``controlled_apartment_catalogue`` (plus an explicit ``availability`` flag,
    so the two fixtures share the same relevance ground truth ``{1, 2}`` under
    the ``relevance_indices`` rule below). Indices 6-32 extend the catalogue
    across Calabar, Enugu and Abuja so that K can genuinely bind (several cases
    have at least 7 eligible candidates) and location, type, price and
    availability hard filters can be exercised independently.

    Each dict uses the same feature keys as ``controlled_apartment_catalogue``
    plus ``availability``, matching the ``Apartment`` fields consumed by the
    recommendation pipeline (``ml.preprocessing``, ``ml.ranking``).

    This is explicitly synthetic, deterministic evaluation/test data
    (AGENTS 40). It is never presented as real-world data.
    """
    return [
        # 1-5: replicate of the controlled catalogue (plus availability).
        dict(title="Calabar 2bd furnished secured", location="Calabar",
             rental_price="180000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Calabar 2bd unfurnished", location="Calabar",
             rental_price="250000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=False, availability=True),
        dict(title="Calabar 3bd expensive", location="Calabar",
             rental_price="450000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Overseas studio", location="Uyo",
             rental_price="120000.00", apartment_type="SELF_CONTAINED",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        dict(title="Calabar 1bd too small", location="Calabar",
             rental_price="150000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        # 6-12: further Calabar candidates.
        dict(title="Calabar 2bd moderate", location="Calabar",
             rental_price="200000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=False, furnished=True, availability=True),
        dict(title="Calabar 2bd premium", location="Calabar",
             rental_price="240000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Calabar 2bd basic", location="Calabar",
             rental_price="170000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=False, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        dict(title="Calabar 1bd compact", location="Calabar",
             rental_price="140000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=True, availability=True),
        dict(title="Calabar studio budget", location="Calabar",
             rental_price="120000.00", apartment_type="SELF_CONTAINED",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=True, availability=True),
        dict(title="Calabar 3bd luxury", location="Calabar",
             rental_price="550000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Calabar 3bd off-grid", location="Calabar",
             rental_price="480000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=False, availability=True),
        # 13-22: Enugu candidates.
        dict(title="Enugu studio budget", location="Enugu",
             rental_price="100000.00", apartment_type="SELF_CONTAINED",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        dict(title="Enugu 1bd compact", location="Enugu",
             rental_price="130000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=True, availability=True),
        dict(title="Enugu 2bd furnished", location="Enugu",
             rental_price="180000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Enugu 2bd premium", location="Enugu",
             rental_price="220000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Enugu 2bd basic", location="Enugu",
             rental_price="160000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=False, availability=True),
        dict(title="Enugu 2bd max", location="Enugu",
             rental_price="300000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Enugu 3bd standard", location="Enugu",
             rental_price="350000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Enugu flat 2bd", location="Enugu",
             rental_price="260000.00", apartment_type="FLAT",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Enugu flat 2bd basic", location="Enugu",
             rental_price="240000.00", apartment_type="FLAT",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        dict(title="Enugu duplex", location="Enugu",
             rental_price="900000.00", apartment_type="DUPLEX",
             bedrooms=4, bathrooms=4, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        # 23-30: Abuja candidates.
        dict(title="Abuja studio", location="Abuja",
             rental_price="150000.00", apartment_type="SELF_CONTAINED",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=False, availability=True),
        dict(title="Abuja 1bd compact", location="Abuja",
             rental_price="200000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=False, furnished=True, availability=True),
        dict(title="Abuja 2bd standard", location="Abuja",
             rental_price="300000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Abuja 2bd no-power", location="Abuja",
             rental_price="350000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=False,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Abuja 3bd furnished", location="Abuja",
             rental_price="600000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Abuja 3bd basic", location="Abuja",
             rental_price="500000.00", apartment_type="THREE_BEDROOM",
             bedrooms=3, bathrooms=3, parking=True, electricity=True,
             water=True, security=True, furnished=False, availability=True),
        dict(title="Abuja duplex luxury", location="Abuja",
             rental_price="1200000.00", apartment_type="DUPLEX",
             bedrooms=4, bathrooms=4, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=True),
        dict(title="Abuja duplex basic", location="Abuja",
             rental_price="800000.00", apartment_type="DUPLEX",
             bedrooms=4, bathrooms=4, parking=True, electricity=True,
             water=True, security=True, furnished=False, availability=True),
        # 31-32: unavailable candidates (exercise the availability hard filter).
        dict(title="Enugu 2bd unavailable", location="Enugu",
             rental_price="250000.00", apartment_type="TWO_BEDROOM",
             bedrooms=2, bathrooms=2, parking=True, electricity=True,
             water=True, security=True, furnished=True, availability=False),
        dict(title="Calabar 1bd unavailable", location="Calabar",
             rental_price="160000.00", apartment_type="ONE_BEDROOM",
             bedrooms=1, bathrooms=1, parking=False, electricity=True,
             water=True, security=True, furnished=True, availability=False),
    ]


def relevance_indices(candidates, truth_profile):
    """Return the 1-based catalogue indices matching a ground-truth profile.

    ``truth_profile`` encodes "what a tenant would judge relevant" and is the
    independent ground truth for the formal evaluation. An apartment is
    relevant when it satisfies every *stated core requirement*:

    - ``location`` contains ``truth_profile["location"]`` (case-insensitive),
      when a location is given;
    - ``apartment_type`` equals the stated type, when one is given;
    - ``bedrooms`` / ``bathrooms`` are at least the stated minimums, when given;
    - ``rental_price`` is at most ``max_rent``, when given;
    - every facility set to True in the profile is provided (soft facilities
      are not relevance-determining).

    Relevance is derived only from these preference-to-attribute comparisons,
    never from the KNN distances, so the ground truth stays independent of the
    algorithm under test. ``availability`` is intentionally NOT part of
    relevance: the engine's availability hard filter governs *eligibility*,
    and the "relevant" set describes the tenant's stated preference match.
    This reproduces the existing ``controlled_apartment_catalogue`` ground
    truth ``{1, 2}`` for a Calabar 2-bed tenant profile.
    """
    location = truth_profile.get("location")
    apartment_type = truth_profile.get("apartment_type")
    min_bedrooms = truth_profile.get("bedrooms")
    min_bathrooms = truth_profile.get("bathrooms")
    max_rent = truth_profile.get("max_rent")

    relevant = set()
    for index, spec in enumerate(candidates, start=1):
        if location and location.lower() not in spec["location"].lower():
            continue
        if apartment_type and spec["apartment_type"] != apartment_type:
            continue
        if min_bedrooms is not None and spec["bedrooms"] < min_bedrooms:
            continue
        if min_bathrooms is not None and spec["bathrooms"] < min_bathrooms:
            continue
        if max_rent is not None and float(spec["rental_price"]) > float(max_rent):
            continue
        for facility in FACILITY_FEATURES:
            if truth_profile.get(facility) is True and not spec[facility]:
                break
        else:
            relevant.add(index)
    return relevant
