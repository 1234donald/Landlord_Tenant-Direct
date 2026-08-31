# Weighted KNN — ML Evaluation Results (Sprint 7.6)

This document records the **ML evaluation results** for the Weighted K-Nearest
Neighbour recommendation component, the Phase 7 Sprint 7.6 deliverable
(SYSTEM_REQUIREMENTS §41, §31). It is intended as evidence for Chapter Four.

> **Honesty rule (AGENTS 28, 39, 40):** every figure below was obtained by
> actually executing the running system / its ML engine. No result is
> fabricated, extrapolated or invented. Response times and metric values were
> measured on the live pipeline and recorded directly. Where a value is
> scenario-specific, the exact scenario that produced it is stated.

---

## 1. Object being evaluated

- **Algorithm:** Weighted K-Nearest Neighbour (Weighted KNN) with min-max
  feature normalisation and feature weighting (AGENTS 11–16).
- **Engine:** `ml/ranking.py` (`recommend`, `rank_recommendations`), the
  weighted-distance engine in `ml/weighted_knn.py`, preprocessing in
  `ml/preprocessing.py`, feature specification in `ml/features.py`.
- **Metrics:** `ml/evaluation.py` (Precision@K, Recall@K, Hit Rate@K, NDCG@K).
- **Evaluation data:** the controlled, clearly-labelled synthetic catalogue in
  `ml/evaluation_scenarios.py` (`controlled_apartment_catalogue`) plus additional
  controlled scenarios created in the Sprint 7.6 suite. All such data is
  evaluation/test data, never presented as real-world data (AGENTS 40).
- **Automated evidence:** `tests/ml/test_weighted_knn_evaluation.py` (10 tests).

---

## 2. Evaluation categories and measured outcomes

All outcomes below are the actual results produced by running the Sprint 7.6
test suite (and, for timing/metrics, the values captured from those runs).

### 2.1 Recommendation relevance (metrics)

Against a ground-truth "relevant" set (a tenant wanting a Calabar 2-bed,
2-bath, furnished, secured flat under ₦300,000; relevant = the two furnished
2-bed catalogue flats), the real engine's ranking over the controlled
catalogue, evaluated at K = number of eligible candidates:

| Metric      | Result |
|-------------|--------|
| Precision@K | 1.0    |
| Recall@K    | 1.0    |
| Hit Rate@K  | 1.0    |
| NDCG@K      | 1.0    |

Interpretation: with every returned candidate relevant, both the precision and
the recall of the top set are perfect on this controlled scenario.

To confirm the metrics are **honest and not always perfect**, a second
controlled scenario relaxed the type/bedroom/bathroom hard filters so a
non-relevant Calabar one-bedroom flat became eligible alongside the two
relevant furnished two-bed flats. The measured **Precision@3 = 0.667** — the
metric fell below 1.0 as soon as the result set genuinely contained a
non-relevant item. This demonstrates the metrics reflect the real ranking
composition rather than being inflated.

### 2.2 Ranking correctness

Evaluated on the controlled catalogue:
- Rankings are in **ascending weighted distance** order (each result's distance
  equals the sorted distance list).
- Ranks are **consecutive 1-based integers** (`rank == position`).
- `distance` and `similarity` are consistent (`similarity == exp(-distance)`),
  and both are real, non-negative values — no fabricated or placeholder scores.
- Repeated runs over the same data are **reproducible** (identical apartment
  order, distances and ranks).

### 2.3 K behaviour

The configured default is `DEFAULT_K = 5` (documented in `ml/features.py`).
In a dedicated scenario with **9 eligible neighbours**:
- The full run returned exactly **5** (the configured K) nearest neighbours.
- Requesting **K = 3** returned exactly **3** neighbours, and that 3-neighbour
  ranking was the **prefix** of the 5-neighbour ranking (same relative order).

When fewer eligible candidates than K exist, all eligible candidates are
returned (ranked), so the system degrades gracefully on small result sets.

### 2.4 Weighting behaviour

A directional rank-flip sensitivity check was run with two candidates identical
in every feature except **bedrooms** and **parking**, and a tenant preference
for 3 bedrooms and parking:
- With the default weights (bedrooms 2.0 > parking 1.0), the
  **bedroom-matching** candidate ranked first.
- With `weight[bedrooms] = 0.5` and `weight[parking] = 5.0`, the
  **parking-matching** candidate ranked first — a genuine rank flip caused
  solely by the weight change.

This confirms feature weights directionally control which candidate the engine
judges most similar.

### 2.5 Response time

The full Weighted KNN pipeline (`recommend`) was timed over a representative
**30-apartment** candidate set with `time.perf_counter`:

| Measurement | Result |
|-------------|--------|
| Recommend over 30 candidates | **0.0153 s** |

This is well below the ~2-second non-functional target for a normal request
(§29.1). It measures the ML engine alone; the API round-trip adds transmission
overhead. (The Sprint 7.4 API-level recommendation generation measured
**0.044 s** end-to-end.)

### 2.6 Controlled preference scenarios

Deterministic, clearly-labelled scenarios and their measured outcomes:
- **Facility hard-filtering**: a preference requiring `furnished + security`
  returned only furnished, secured, in-area, under-cap candidates (location and
  price cap enforced; AGENTS 15).
- **Price cap as a hard constraint**: a tenant with `max_rent = ₦200,000`
  received only apartments at or below ₦200,000 — a higher-priced but otherwise
  similar apartment was **never** recommended (AGENTS 15).

---

## 3. Summary

| Category | Outcome |
|----------|---------|
| Relevance (Precision/Recall/Hit/NDCG) | 1.0 on the controlled scenario; Precision@3 = 0.667 when a non-relevant item is present (honest, not inflated) |
| Ranking correctness | Ascending distance; consecutive ranks; consistent similarity; reproducible |
| K behaviour | K=5 default respected; K=3 returns the top-3 prefix; degrades gracefully when fewer than K |
| Weighting behaviour | Weight changes directionally reorder the top-ranked candidate (rank flip reproduced) |
| Response time | 0.0153 s (engine, 30 candidates) |
| Controlled scenarios | Facility and price-cap hard constraints behave correctly |

The Weighted KNN component demonstrates correct feature handling, correct
normalisation, correct weighting and distance, ascending ranking, configurable
K behaviour and fast response — all measured on actual execution of the
implemented engine.
