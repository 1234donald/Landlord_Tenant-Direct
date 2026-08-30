"""
Machine-learning recommendation component (Weighted KNN).

This package is kept outside the Django apps to preserve separation between
the recommendation component and the web/presentation layer (AGENTS.md A6).

The Weighted KNN implementation lives in the module files below:

- ``features.py``         - feature specification and configurable weights;
- ``preprocessing.py``    - categorical encoding and min-max normalisation;
- ``weighted_knn.py``     - the weighted Euclidean distance engine;
- ``ranking.py``          - hard filtering, candidate selection and ranking;
- ``evaluation.py``       - Precision@K, Recall@K, Hit Rate@K and NDCG@K;
- ``evaluation_scenarios``- reproducible test/evaluation scenario data.

All modules are pure Python (no Django imports) so they can be unit-tested
in isolation and reused from the Django service layer.
"""
