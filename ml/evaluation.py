"""
Recommendation evaluation metrics (Phase 5, Sprint 5.7).

This module is the **evaluation** deliverable of Sprint 5.7 ("Recommendation
Validation and Evaluation Readiness"). It supplies the four ranking metrics
required by SYSTEM_REQUIREMENTS §31 and TECH_STACK §K/B.3:

- ``Precision@K`` — fraction of the top-K retrieved apartments that are
  relevant;
- ``Recall@K``   — fraction of all relevant apartments that appear in the
  top-K retrieved apartments;
- ``Hit Rate@K`` — whether at least one relevant apartment appears in the
  top-K retrieved apartments (0 or 1);
- ``NDCG@K``     — normalised discounted cumulative gain over the top-K
  retrieved apartments (higher-ranked relevant hits contribute more).

The metrics operate on *retrieved ranking results* compared against a set of
*ground-truth relevant* identities. They are pure Python (no Django imports),
mirroring the decoupling of the other ``ml`` modules (TECH_STACK §K), so the
metrics can be unit-tested with plain identifiers and used both in automated
tests and in the Chapter Four evaluation.

No metric is fabricated (AGENTS 17, 39, SYSTEM_REQUIREMENTS §31): every value is
computed from actual ranking output and an explicitly supplied relevance set.
Terminology stays factual — these are similarity/rank-matching statistics, not
a claim of guaranteed tenant satisfaction.
"""
import math


def _identities(ranking_results):
    """Normalise ranking results into an ordered list of comparable identities.

    Accepts either the result-dict shape produced by ``ml.ranking``
    (``{"apartment": <object|id>, "distance": float, ...}``) or a plain iterable
    of apartment objects/identifiers. Returns an ordered list of identities
    mirroring the ranking order (best first).
    """
    ordered = []
    for entry in ranking_results:
        if isinstance(entry, dict):
            apartment = entry["apartment"]
        else:
            apartment = entry
        ordered.append(getattr(apartment, "pk", apartment))
    return ordered


def _top_k(results, k):
    """Return the first ``k`` identities (or all, when fewer than ``k`` exist)."""
    identities = _identities(results)
    if k is None or k < 0:
        k = len(identities)
    return identities[:k]


def precision_at_k(results, relevant, k):
    """Precision@K: proportion of the top-K results that are relevant.

    ``relevant`` is a set of ground-truth relevant identities. When ``k`` is
    larger than the number of retrieved results, only the retrieved results are
    scored (the denominator remains the number of scored positions). Returns 0
    when nothing was retrieved or ``k <= 0``.
    """
    relevant = set(relevant)
    top = _top_k(results, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in relevant)
    return hits / len(top)


def recall_at_k(results, relevant, k):
    """Recall@K: fraction of all relevant identities found in the top-K.

    Returns 0 when ``relevant`` is empty (there is nothing to recall) or when
    ``k <= 0``.
    """
    relevant = set(relevant)
    if not relevant or k <= 0:
        return 0.0
    top = _top_k(results, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in relevant)
    return hits / len(relevant)


def hit_rate_at_k(results, relevant, k):
    """Hit Rate@K: 1 if any relevant identity appears in the top-K, else 0."""
    relevant = set(relevant)
    if not relevant or k <= 0:
        return 0.0
    top = _top_k(results, k)
    return 1.0 if any(item in relevant for item in top) else 0.0


def _dcg_at_k(top, relevant):
    """Discounted cumulative gain over an ordered top-K list (binary relevance).

    Uses the standard base-2 log discount ``1 / log2(position + 1)`` so
    position 1 contributes 1.0, position 2 ~0.631, position 3 0.5, etc.
    """
    total = 0.0
    for position, item in enumerate(top, start=1):
        if item in relevant:
            total += 1.0 / math.log2(position + 1)
    return total


def ndcg_at_k(results, relevant, k):
    """NDCG@K: normalised discounted cumulative gain over the top-K.

    Uses binary relevance (a relevant within the retrieved list adds gain).
    The ideal DCG places all relevant identities first; NDCG is their ratio so
    the result is bounded to [0, 1]. Returns 0 when ``k <= 0`` or nothing is
    relevant/retrieved.
    """
    relevant = set(relevant)
    if not relevant or k <= 0:
        return 0.0
    top = _top_k(results, k)
    if not top:
        return 0.0

    dcg = _dcg_at_k(top, relevant)
    # Ideal ordering: the relevant identities that could appear in the top-K,
    # first, then the rest to fill up to length(top).
    ideal = list(relevant)[:len(top)]
    ideal += [None] * (len(top) - len(ideal))
    idcg = _dcg_at_k(ideal, relevant)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate(results, relevant, k=None):
    """Return all four metrics for a ranking against a relevance set.

    ``k`` defaults to the full retrieved list length when omitted. Returns a
    dict keyed ``precision``, ``recall``, ``hit_rate`` and ``ndcg``.

    Example:
        evaluate([{"apartment": 2, "distance": 0.1},
                  {"apartment": 5, "distance": 0.4}],
                 relevant={2}, k=2)
        # -> {"precision": 0.5, "recall": 1.0, "hit_rate": 1.0, "ndcg": 1.0}
    """
    if k is None:
        k = len(_identities(results))
    return {
        "precision": precision_at_k(results, relevant, k),
        "recall": recall_at_k(results, relevant, k),
        "hit_rate": hit_rate_at_k(results, relevant, k),
        "ndcg": ndcg_at_k(results, relevant, k),
    }
