"""
Dev seed script — insert sample places, ratings, outings, and saves.

Structured as reusable helpers (TYP-68) that TYP-69 will use to hand-curate
a synthetic training dataset for the mvML models. `main()` demonstrates the
helpers by recreating the original TYP-58/59/60 seed rows for Alan's real user.

Idempotency:
- users, places, saved_places, outings: matched by natural key; safe to re-run
- place_ratings: append-only per TYP-21; every run adds a new row (dedup happens
  at read-time via DISTINCT ON)

Usage:
    cd backend && source venv/bin/activate
    python scripts/seed_dev_data.py [--email you@example.com]

Prints the connected database host as a sanity check before writing.
"""

import argparse
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models.events import Event  # noqa: E402
from app.models.outing_invitations import OutingInvitation  # noqa: E402
from app.models.outings import Outing  # noqa: E402
from app.models.place_ratings import PlaceRating  # noqa: E402
from app.models.places import Place  # noqa: E402
from app.models.saved_places import SavedPlace  # noqa: E402
from app.models.users import User  # noqa: E402

# --- Helpers (TYP-68) --------------------------------------------------------
#
# These are the reusable primitives TYP-69 uses to hand-curate synthetic
# training data. All are idempotent except create_rating (append-only).


def create_user(
    db: Session,
    email: str,
    display_name: str,
    bio: str | None = None,
) -> User:
    """Idempotent by email. Updates display_name/bio if the row already exists."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, display_name=display_name, bio=bio)
        db.add(user)
        db.flush()
        print(f"  + user: {email}")
        return user

    if user.display_name != display_name:
        old = user.display_name
        print(f"  ~ user {email}: display_name {old!r} → {display_name!r}")
        user.display_name = display_name
    if bio is not None and user.bio != bio:
        user.bio = bio
    return user


def create_place(
    db: Session,
    name: str,
    category: str,
    lat: float,
    lng: float,
    source_url: str | None = None,
) -> Place:
    """Idempotent by name."""
    place = db.scalar(select(Place).where(Place.name == name))
    if place is None:
        place = Place(
            name=name,
            category=category,
            latitude=lat,
            longitude=lng,
            source_url=source_url,
        )
        db.add(place)
        db.flush()
        print(f"  + place: {name}")
    return place


def create_rating(
    db: Session,
    user_id: uuid.UUID,
    place_id: uuid.UUID,
    rating: float,
    created_at: datetime | None = None,
) -> PlaceRating:
    """Append-only per TYP-21. Every call inserts a new row."""
    pr = PlaceRating(user_id=user_id, place_id=place_id, rating=rating)
    if created_at is not None:
        pr.created_at = created_at
    db.add(pr)
    return pr


def create_saved(
    db: Session,
    user_id: uuid.UUID,
    place_id: uuid.UUID,
    created_at: datetime | None = None,
) -> SavedPlace:
    """Idempotent on the (user_id, place_id) composite PK."""
    existing = db.scalar(
        select(SavedPlace).where(
            SavedPlace.user_id == user_id,
            SavedPlace.place_id == place_id,
        )
    )
    if existing is not None:
        return existing
    sp = SavedPlace(user_id=user_id, place_id=place_id)
    if created_at is not None:
        sp.created_at = created_at
    db.add(sp)
    return sp


def create_outing_with_stops(
    db: Session,
    creator_id: uuid.UUID,
    title: str,
    stops: list[tuple[uuid.UUID, float]],
    final_rating: float,
    scheduled_for: datetime | None = None,
    completed_at: datetime | None = None,
) -> Outing:
    """Idempotent on (creator_id, title).

    Creates: 1 completed outing + N completed events (with sequence_position + weight)
    + creator auto-invitation with rsvp_status='accepted' (matches TYP-19 API behavior).

    `stops` is a list of (place_id, weight) tuples in intended sequence order.
    Weights are not normalized here — the caller decides the shape.
    """
    existing = db.scalar(
        select(Outing).where(
            Outing.creator_id == creator_id,
            Outing.title == title,
        )
    )
    if existing is not None:
        return existing

    if completed_at is None:
        completed_at = datetime.now(UTC)
    if scheduled_for is None:
        scheduled_for = completed_at

    outing = Outing(
        creator_id=creator_id,
        title=title,
        status="completed",
        scheduled_for=scheduled_for,
        completed_at=completed_at,
        final_rating=final_rating,
    )
    db.add(outing)
    db.flush()

    for position, (place_id, weight) in enumerate(stops, start=1):
        event = Event(
            creator_id=creator_id,
            place_id=place_id,
            outing_id=outing.outing_id,
            sequence_position=position,
            status="completed",
            scheduled_for=scheduled_for,
            completed_at=completed_at,
            weight=weight,
        )
        db.add(event)

    db.add(
        OutingInvitation(
            user_id=creator_id,
            outing_id=outing.outing_id,
            rsvp_status="accepted",
        )
    )

    print(f"  + outing: {title} = {final_rating} ({len(stops)} stops)")
    return outing


# --- Sample data (Alan's real user; recreates TYP-58/59/60 rows) -------------

# `category` must stay inside the 5-value taxonomy the ML models are defined
# over (Activity / Restaurant / Cafe / Dessert / Bar) — `places.category` has no
# CHECK constraint, so nothing enforces this but us. Trillium was "Brewery"
# until TYP-70, which put it outside the taxonomy and gave it no ground-truth
# preference to learn from.
#
# "TopGolf Canton" is spelled to match `seed_ml_data.py` deliberately:
# `create_place` is idempotent by name, so matching names means Alan's rating
# and the personas' ratings land on ONE place row instead of two near-duplicates.
PLACES_AND_RATINGS = [
    ("Trillium Brewing", "Bar", 42.3491, -71.0517, 9.1),
    ("TopGolf Canton", "Activity", 42.1535, -71.1389, 8.4),
    ("Bar Lyon", "Restaurant", 42.3406, -71.0734, 8.0),
    ("Tasty Burger", "Restaurant", 42.3505, -71.0594, 7.6),
    ("Tatte Bakery", "Cafe", 42.3580, -71.0680, 7.2),
]

# (title, days_ago, final_rating, [place_name, ...])
OUTINGS = [
    ("Friday Brewery Night", 3, 8.7, ["Trillium Brewing", "Tasty Burger"]),
    ("Saturday Day Out", 10, 9.2, ["TopGolf Canton", "Bar Lyon"]),
    ("Coffee & Drinks", 21, 7.5, ["Tatte Bakery", "Bar Lyon"]),
]

SAVES = ["Trillium Brewing", "Tatte Bakery"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="talan4030@gmail.com")
    parser.add_argument("--display-name", default="Alan Tai")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL", "")
    host = urlparse(db_url.replace("+psycopg", "")).hostname or "?"
    print(f"DB host: {host}")
    if host not in ("localhost", "127.0.0.1"):
        confirm = input("Non-local DB. Type 'yes' to proceed: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    db = SessionLocal()

    # Real user must already exist (created by JWT auto-provisioning). Fetch
    # rather than create so we don't accidentally spawn a duplicate under a
    # different user_id from the one Supabase issued.
    user = db.scalar(select(User).where(User.email == args.email))
    if user is None:
        print(f"User not found: {args.email}")
        sys.exit(1)
    if user.display_name != args.display_name:
        print(f"  ~ display_name: {user.display_name!r} → {args.display_name!r}")
        user.display_name = args.display_name
    print(f"Seeding for user: {user.email} ({user.display_name})")

    places_by_name: dict[str, Place] = {}
    for name, category, lat, lng, score in PLACES_AND_RATINGS:
        place = create_place(db, name, category, lat, lng)
        places_by_name[name] = place
        create_rating(db, user.user_id, place.place_id, score)
        print(f"  + rating: {name} = {score}")

    for title, days_ago, final_rating, place_names in OUTINGS:
        completed_at = datetime.now(UTC) - timedelta(days=days_ago)
        stops = [
            (places_by_name[p].place_id, 1.0 / len(place_names)) for p in place_names
        ]
        create_outing_with_stops(
            db,
            creator_id=user.user_id,
            title=title,
            stops=stops,
            final_rating=final_rating,
            scheduled_for=completed_at,
            completed_at=completed_at,
        )

    for name in SAVES:
        place = places_by_name.get(name)
        if place is None:
            print(f"  ! missing place for save: {name}")
            continue
        create_saved(db, user.user_id, place.place_id)

    db.commit()
    print("Done.")


if __name__ == "__main__":
    main()
