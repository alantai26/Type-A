"""Training-data loading for the Atomic Recommender (TYP-70)."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

# The closed taxonomy the TYP-69 PREFERENCE_MATRIX is defined over. Stored
# capitalized because iOS renders `place.category` straight to the user
# (ProfileView.swift:240, PlaceDetailView.swift:58); compared lowercased
# because `places.category` is free text with no CHECK constraint.
CANONICAL_CATEGORIES: tuple[str, ...] = (
    "Activity",
    "Restaurant",
    "Cafe",
    "Dessert",
    "Bar",
)

_BY_LOWER = {c.lower(): c for c in CANONICAL_CATEGORIES}


def normalize_category(raw: str | None) -> str | None:
    """Fold a raw `places.category` value onto the canonical taxonomy.

    Case-insensitive, so a stray lowercase `restaurant` row can't become a
    second one-hot column alongside `Restaurant`. Returns None for anything
    outside the taxonomy — callers surface those rather than guessing a mapping,
    since a wrong guess would train the model on a preference that was never
    defined.
    """
    if not raw:
        return None
    return _BY_LOWER.get(raw.strip().lower())


@dataclass(frozen=True)
class RatingRow:
    """One training observation: this user rated this place this highly."""

    user_id: str
    place_id: str
    category: str
    rating: float


# `place_ratings` is append-only per TYP-21 — re-running a seed script inserts
# duplicate rows rather than updating. Training on raw rows would silently
# double-weight every re-seeded observation, so take the latest rating per
# (user, place). This mirrors what the read endpoints already do:
# `GET /me/place_ratings` and `/places/{id}/friends_activity`.
_TRAINING_SQL = text("""
    SELECT DISTINCT ON (pr.user_id, pr.place_id)
        pr.user_id::text  AS user_id,
        pr.place_id::text AS place_id,
        p.category        AS category,
        pr.rating         AS rating
    FROM place_ratings pr
    JOIN places p ON p.place_id = pr.place_id
    ORDER BY pr.user_id, pr.place_id, pr.created_at DESC
""")


def load_training_rows(db: Session) -> tuple[list[RatingRow], dict[str, int]]:
    """Load deduped, category-validated training rows.

    Returns `(rows, skipped)`, where `skipped` counts dropped rows keyed by
    their raw category value. The training script prints it so an off-taxonomy
    category shrinking the training set is visible rather than silent.
    """
    rows: list[RatingRow] = []
    skipped: dict[str, int] = {}

    for record in db.execute(_TRAINING_SQL).mappings():
        category = normalize_category(record["category"])
        if category is None:
            raw = record["category"] or "<null>"
            skipped[raw] = skipped.get(raw, 0) + 1
            continue
        rows.append(
            RatingRow(
                user_id=record["user_id"],
                place_id=record["place_id"],
                category=category,
                rating=float(record["rating"]),
            )
        )

    return rows, skipped
