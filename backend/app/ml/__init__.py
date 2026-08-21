"""ML models for TypeA (TYP-70 onward).

Split by lifecycle:

- `data.py`            — training-data loading + category normalization
- `atomic_recommender.py` — the Atomic Recommender: feature encoding, fit, predict

Training runs offline (`backend/scripts/train_atomic.py`) and needs
scikit-learn. Inference runs in the request path and needs only numpy — the
model artifact is a plain JSON blob of coefficients, deliberately not a
sklearn pickle. See `requirements-ml.txt`.
"""
