"""ML models for TypeA (TYP-70 onward).

Split by lifecycle:

- `data.py`               — training-data loading + category validation
- `atomic_recommender.py` — feature encoding, ridge fit, inference

Training runs offline (`backend/scripts/train_atomic.py`) and needs
scikit-learn. Inference runs in the request path and needs only numpy — the
model artifact is a plain JSON blob of coefficients, deliberately not a
sklearn pickle, so sklearn + scipy (~143MB) stay out of the Render runtime.
See `requirements-ml.txt`.
"""
