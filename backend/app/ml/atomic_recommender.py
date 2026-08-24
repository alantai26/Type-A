"""Atomic Recommender — per-user place-rating prediction (TYP-70, TYP-77).

Predicts how much a given user will rate a given place, using only the place's
category. See `docs/TYP_70_HANDOFF.md` for the modeling rationale.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from app.ml.data import CANONICAL_CATEGORIES, RatingRow


def build_features(
    rows: list[RatingRow],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Encode rating rows into a design matrix.

    Returns `(X, y, column_names)`:

    - `X` — shape (n_rows, n_columns), all 0.0/1.0
    - `y` — shape (n_rows,), the actual ratings
    - `column_names` — length n_columns, labels the meaning of each column

    Column layout, in this order:

        [ user one-hot | category one-hot | user x category one-hot ]
           n_users          5 cols            n_users * 5 cols

    Naming convention for `column_names` (the eval script parses these):

        "user=<user_id>"
        "cat=<Category>"
        "user=<user_id>|cat=<Category>"

    Ordering must be deterministic so a saved model's coefficients still line up
    with freshly-built columns later: sort user_ids, and keep categories in
    CANONICAL_CATEGORIES order (not sorted, not set order).

    Each row has exactly three 1.0 values — one per block.
    """
    # --- setup: work out the column layout before touching any rows ---------
    user_ids = sorted({row.user_id for row in rows})
    n_users = len(user_ids)
    n_cats = len(CANONICAL_CATEGORIES)
    n_cols = n_users + n_cats + n_users * n_cats

    # 0-based position WITHIN each block, not the final column number.
    # enumerate() hands you (0, first_id), (1, second_id), ... so the dict
    # comprehension builds {first_id: 0, second_id: 1, ...} from the data.
    user_index = {user_id: i for i, user_id in enumerate(user_ids)}
    cat_index = {cat: j for j, cat in enumerate(CANONICAL_CATEGORIES)}

    # Same order as the formula below: users, then categories, then
    # interactions nested user-outer / category-inner.
    column_names = (
        [f"user={u}" for u in user_ids]
        + [f"cat={c}" for c in CANONICAL_CATEGORIES]
        + [f"user={u}|cat={c}" for u in user_ids for c in CANONICAL_CATEGORIES]
    )

    X = np.zeros((len(rows), n_cols))
    y = np.zeros(len(rows))

    for r, row in enumerate(rows):
        i = user_index[row.user_id]
        j = cat_index[row.category]
        X[r, i] = 1.0
        X[r, n_users + j] = 1.0
        X[r, n_users + n_cats + i * n_cats + j] = 1.0
        y[r] = row.rating

    return X, y, column_names

# Log-spaced so each candidate is a meaningful step from the last — trying
# 1, 2, 3 would explore almost none of the useful range, while 0.01 -> 100
# spans "trust the data" to "trust the global average".
ALPHA_GRID: tuple[float, ...] = (0.01, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)


@dataclass(frozen=True)
class FittedModel:
    """A trained model as plain numbers — no sklearn objects.

    Deliberately serializable to JSON so inference needs only numpy. See the
    package docstring for why.
    """

    columns: list[str]
    coef: list[float]
    intercept: float
    alpha: float
    n_train: int


def fit(
    X: np.ndarray,
    y: np.ndarray,
    column_names: list[str],
    alphas: tuple[float, ...] = ALPHA_GRID,
) -> FittedModel:
    """Fit ridge regression, choosing alpha by cross-validation.

    `RidgeCV` refits on the full training set once the best alpha is chosen, so
    the returned coefficients use all the data.

    Imports sklearn lazily: this function only runs during offline training, and
    the module is imported by the request path for inference.
    """
    from sklearn.linear_model import RidgeCV

    model = RidgeCV(alphas=alphas)
    model.fit(X, y)

    return FittedModel(
        columns=list(column_names),
        coef=[float(c) for c in model.coef_],
        intercept=float(model.intercept_),
        alpha=float(model.alpha_),
        n_train=int(X.shape[0]),
    )

RATING_MIN = 0.0
RATING_MAX = 10.0


def predict(model: FittedModel, user_id: str, category: str) -> float:
    lookup = dict(zip(model.columns, model.coef, strict=True))
    score = (
        model.intercept
        + lookup.get(f"user={user_id}", 0.0)
        + lookup.get(f"cat={category}", 0.0)
        + lookup.get(f"user={user_id}|cat={category}", 0.0)
    )
    return max(RATING_MIN, min(RATING_MAX, score))


# --- Artifact IO -------------------------------------------------------------
#
# Bumped whenever the artifact's meaning changes — new feature blocks, a
# different column-naming scheme, a changed rating scale. `load_json` refuses a
# mismatch rather than serving plausible-looking wrong numbers from coefficients
# that no longer mean what the code thinks they mean.
MODEL_VERSION = "atomic-v1"

# Repo root, not backend/ — `coefficients/` is a top-level ML pipeline dir.
ARTIFACT_PATH = Path(__file__).resolve().parents[3] / "coefficients" / "atomic_v1.json"


def save_json(model: FittedModel, path: Path = ARTIFACT_PATH) -> Path:
    """Write a fitted model to disk as JSON. Returns the path written.

    Deliberately not a pickle. Unpickling a sklearn estimator would require
    sklearn at import time in the request path, dragging sklearn + scipy
    (~143MB) onto a 512MB Render dyno to serve what is ultimately three dict
    lookups and an add. Plain JSON keeps inference numpy-only.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model_version": MODEL_VERSION, **asdict(model)}
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def load_json(path: Path = ARTIFACT_PATH) -> FittedModel:
    """Read an artifact written by `save_json`.

    Raises `FileNotFoundError` if the artifact is missing and `ValueError` if it
    was written by a different model version — both are startup-time failures,
    which is where you want them. A silently stale artifact would serve wrong
    predictions indefinitely with nothing in the logs.
    """
    payload = json.loads(path.read_text())

    found = payload.get("model_version")
    if found != MODEL_VERSION:
        raise ValueError(
            f"{path} was written by {found!r}, but this code expects "
            f"{MODEL_VERSION!r}. Retrain with scripts/train_atomic.py."
        )

    return FittedModel(
        columns=payload["columns"],
        coef=payload["coef"],
        intercept=payload["intercept"],
        alpha=payload["alpha"],
        n_train=payload["n_train"],
    )