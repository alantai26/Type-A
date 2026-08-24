"""
Train the Atomic Recommender and write the servable artifact (TYP-77).

Offline batch training. Reads `place_ratings`, fits ridge regression with alpha
chosen by cross-validation, and writes plain coefficients to
`coefficients/atomic_v1.json` at the repo root. The API loads that file; it
never trains and never imports scikit-learn.

Rerun whenever enough new ratings have landed to be worth relearning from.

Usage:
    cd backend && source venv/bin/activate
    pip install -r requirements-ml.txt        # sklearn, training only
    python scripts/train_atomic.py [--dry-run] [--out PATH]

Prints the chosen alpha, training-set size, any skipped off-taxonomy rows, and
a sample prediction per user so an obviously broken run is visible immediately.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.ml.atomic_recommender import (  # noqa: E402
    ARTIFACT_PATH,
    build_features,
    fit,
    predict,
    save_json,
)
from app.ml.data import CANONICAL_CATEGORIES, load_training_rows  # noqa: E402
from app.models.users import User  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="train and report, but don't write the artifact",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARTIFACT_PATH,
        help=f"artifact path (default: {ARTIFACT_PATH})",
    )
    args = parser.parse_args()

    db = SessionLocal()

    # --- load ---------------------------------------------------------------
    rows, skipped = load_training_rows(db)
    if not rows:
        print("No training rows. Seed the database first:")
        print("  python scripts/seed_dev_data.py && python scripts/seed_ml_data.py")
        sys.exit(1)

    print(f"Loaded {len(rows)} ratings.")

    # Off-taxonomy rows are dropped, not guessed at — but silently shrinking the
    # training set is how a category typo turns into a quietly worse model, so
    # say so loudly.
    if skipped:
        total = sum(skipped.values())
        print(f"\n  !! skipped {total} rating(s) with unrecognized categories:")
        for raw, count in sorted(skipped.items(), key=lambda kv: -kv[1]):
            print(f"       {raw!r}: {count}")
        print(f"     valid categories: {', '.join(CANONICAL_CATEGORIES)}")
        print("     fix the category on those places and rerun.\n")

    # --- fit ----------------------------------------------------------------
    X, y, columns = build_features(rows)
    n_users = len({row.user_id for row in rows})
    print(
        f"Design matrix: {X.shape[0]} rows x {X.shape[1]} columns "
        f"({n_users} users + {len(CANONICAL_CATEGORIES)} categories + "
        f"{n_users * len(CANONICAL_CATEGORIES)} interactions)"
    )

    model = fit(X, y, columns)
    print(f"Fit: alpha={model.alpha}, intercept={model.intercept:.2f}")

    # --- smoke test ---------------------------------------------------------
    names = {
        str(u.user_id): u.display_name for u in db.scalars(select(User)).all()
    }
    print(f"\nSample predictions ({', '.join(CANONICAL_CATEGORIES)}):")

    favorites = []
    for user_id in sorted({row.user_id for row in rows}):
        scores = [predict(model, user_id, c) for c in CANONICAL_CATEGORIES]
        best = CANONICAL_CATEGORIES[scores.index(max(scores))]
        favorites.append(best)
        rendered = "  ".join(f"{s:5.2f}" for s in scores)
        print(f"  {names.get(user_id, user_id)[:16]:<17}{rendered}   -> {best}")

    # If every user's top category is the same one, the interaction block isn't
    # reaching the prediction and all that's left is a per-user offset applied
    # to a shared category ranking. Checking "do predictions vary by user" is
    # NOT enough — the user term alone produces variation between users while
    # leaving every user's preference ORDER identical, which is exactly the
    # shape of a broken interaction lookup.
    if len(set(favorites)) == 1:
        print(
            f"\n  !! every user's top category is {favorites[0]!r}. The "
            "interaction block isn't contributing — check that predict() "
            "builds the same column names build_features() emits."
        )

    # --- save ---------------------------------------------------------------
    if args.dry_run:
        print("\nDry run — artifact not written.")
        return

    written = save_json(model, args.out)
    size_kb = written.stat().st_size / 1024
    print(f"\nWrote {written} ({size_kb:.1f} KB, {len(model.coef)} coefficients).")
    print("Commit it — Render serves from the repo and never trains.")


if __name__ == "__main__":
    main()
