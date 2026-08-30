"""
ML tests for Phase 5, Sprint 5.7 - recommendation evaluation metrics.

These verify ``ml.evaluation``: Precision@K, Recall@K, Hit Rate@K and NDCG@K
against known-value scenarios (SYSTEM_REQUIREMENTS §31, TECH_STACK §K/B.3). The
scenarios come from ``ml.evaluation_scenarios`` and are pure, reproducible test
data (AGENTS 40). Every expected value is computed independently here and by the
module, so the module output is asserted exactly. These are pure-Python tests
(fast; no database) because the metrics have no Django dependency.
"""
import math

from ml import evaluation
from ml.evaluation_scenarios import (
    metric_scenario_empty_relevant,
    metric_scenario_k_larger_than_retrieved,
    metric_scenario_no_hit,
    metric_scenario_perfect_ranking,
    metric_scenario_simple,
)


def test_simple_scenario_precision():
    ranking, relevant, k, expected = metric_scenario_simple()
    assert evaluation.precision_at_k(ranking, relevant, k) == expected["precision"]


def test_perfect_ranking_precision_is_one():
    ranking, relevant, k, expected = metric_scenario_perfect_ranking()
    assert evaluation.precision_at_k(ranking, relevant, k) == expected["precision"]


def test_no_hit_precision_is_zero():
    ranking, relevant, k, _ = metric_scenario_no_hit()
    assert evaluation.precision_at_k(ranking, relevant, k) == 0.0


def test_k_larger_than_retrieved_precision_uses_retrieved_denominator():
    ranking, relevant, k, expected = metric_scenario_k_larger_than_retrieved()
    assert evaluation.precision_at_k(ranking, relevant, k) == expected["precision"]


def test_k_zero_precision_is_zero():
    ranking, relevant, _, _ = metric_scenario_no_hit()
    assert evaluation.precision_at_k(ranking, relevant, 0) == 0.0


def test_simple_scenario_recall():
    ranking, relevant, k, expected = metric_scenario_simple()
    assert math.isclose(
        evaluation.recall_at_k(ranking, relevant, k), expected["recall"]
    )


def test_empty_relevant_recall_is_zero():
    ranking, relevant, k, _ = metric_scenario_empty_relevant()
    assert evaluation.recall_at_k(ranking, relevant, k) == 0.0


def test_perfect_ranking_recall_is_one():
    ranking, relevant, k, expected = metric_scenario_perfect_ranking()
    assert evaluation.recall_at_k(ranking, relevant, k) == expected["recall"]


def test_simple_scenario_hit_rate():
    ranking, relevant, k, expected = metric_scenario_simple()
    assert evaluation.hit_rate_at_k(ranking, relevant, k) == expected["hit_rate"]


def test_no_hit_hit_rate_is_zero():
    ranking, relevant, k, _ = metric_scenario_no_hit()
    assert evaluation.hit_rate_at_k(ranking, relevant, k) == 0.0


def test_empty_relevant_hit_rate_is_zero():
    ranking, relevant, k, _ = metric_scenario_empty_relevant()
    assert evaluation.hit_rate_at_k(ranking, relevant, k) == 0.0


def test_simple_scenario_ndcg():
    ranking, relevant, k, expected = metric_scenario_simple()
    assert math.isclose(
        evaluation.ndcg_at_k(ranking, relevant, k), expected["ndcg"]
    )


def test_perfect_ranking_ndcg_is_one():
    ranking, relevant, k, expected = metric_scenario_perfect_ranking()
    assert evaluation.ndcg_at_k(ranking, relevant, k) == expected["ndcg"]


def test_no_hit_ndcg_is_zero():
    ranking, relevant, k, _ = metric_scenario_no_hit()
    assert evaluation.ndcg_at_k(ranking, relevant, k) == 0.0


def test_higher_ranked_relevant_wins_more_ndcg_gain():
    first = evaluation.ndcg_at_k(
        [{"apartment": 1}, {"apartment": 2}, {"apartment": 3}], {1}, 3
    )
    later = evaluation.ndcg_at_k(
        [{"apartment": 1}, {"apartment": 2}, {"apartment": 3}], {3}, 3
    )
    assert first > later


def test_evaluate_returns_all_metrics():
    ranking, relevant, k, expected = metric_scenario_simple()
    result = evaluation.evaluate(ranking, relevant, k)
    assert set(result) == {"precision", "recall", "hit_rate", "ndcg"}
    assert result["precision"] == expected["precision"]
    assert math.isclose(result["recall"], expected["recall"])
    assert result["hit_rate"] == expected["hit_rate"]
    assert math.isclose(result["ndcg"], expected["ndcg"])


def test_evaluate_defaults_k_to_retrieved_length():
    ranking, relevant, k, expected = metric_scenario_perfect_ranking()
    result = evaluation.evaluate(ranking, relevant)
    assert result["precision"] == expected["precision"]
    assert result["recall"] == expected["recall"]
    assert result["hit_rate"] == expected["hit_rate"]
    assert math.isclose(result["ndcg"], expected["ndcg"])


def test_evaluate_reads_model_instance_pk():
    class FakeApartment:
        def __init__(self, pk):
            self.pk = pk

    ranking = [FakeApartment(1), FakeApartment(2)]
    result = evaluation.evaluate(ranking, {1}, 2)
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0
    assert result["hit_rate"] == 1.0
    assert math.isclose(result["ndcg"], 1.0)


def test_metric_scenarios_are_reproducible():
    for builder in (
        metric_scenario_simple,
        metric_scenario_no_hit,
        metric_scenario_empty_relevant,
        metric_scenario_k_larger_than_retrieved,
        metric_scenario_perfect_ranking,
    ):
        assert builder() == builder()
