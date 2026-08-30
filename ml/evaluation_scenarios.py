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
