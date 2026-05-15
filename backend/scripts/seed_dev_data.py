"""
Dev seed script — insert sample places + ratings for a local user.

Place inserts are idempotent (matched by name — re-running won't duplicate).
Rating inserts always append a new row (append-only by design per TYP-21);
DISTINCT ON dedupe at read time gives the latest score per place.

Usage:
    cd backend && source venv/bin/activate
    python scripts/seed_dev_data.py [--email you@example.com]

Prints the connected database host as a sanity check before writing.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models.events import Event  # noqa: E402
from app.models.outings import Outing  # noqa: E402
from app.models.place_ratings import PlaceRating  # noqa: E402
from app.models.places import Place  # noqa: E402
from app.models.saved_places import SavedPlace  # noqa: E402
from app.models.users import User  # noqa: E402

PLACES_AND_RATINGS = [
    ("Trillium Brewing", "Brewery", 42.3491, -71.0517, 9.1),
    ("Top Golf", "Activity", 42.1535, -71.1389, 8.4),
    ("Bar Lyon", "Restaurant", 42.3406, -71.0734, 8.0),
    ("Tasty Burger", "Restaurant", 42.3505, -71.0594, 7.6),
    ("Tatte Bakery", "Cafe", 42.3580, -71.0680, 7.2),
]

# (title, days_ago, final_rating, [place_name, ...])
# days_ago controls completed_at — most-recent first in TYP-59's Profile list.
OUTINGS = [
    ("Friday Brewery Night", 3, 8.7, ["Trillium Brewing", "Tasty Burger"]),
    ("Saturday Day Out", 10, 9.2, ["Top Golf", "Bar Lyon"]),
    ("Coffee & Drinks", 21, 7.5, ["Tatte Bakery", "Bar Lyon"]),
]

# Places bookmarked by the user — populates TYP-60's Profile Saved list.
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

    user = db.scalar(select(User).where(User.email == args.email))
    if user is None:
        print(f"User not found: {args.email}")
        sys.exit(1)

    if user.display_name != args.display_name:
        print(f"  ~ display_name: {user.display_name!r} → {args.display_name!r}")
        user.display_name = args.display_name

    print(f"Seeding for user: {user.email} ({user.display_name})")

    for name, category, lat, lng, score in PLACES_AND_RATINGS:
        place = db.scalar(select(Place).where(Place.name == name))
        if place is None:
            place = Place(name=name, category=category, latitude=lat, longitude=lng)
            db.add(place)
            db.flush()
            print(f"  + place: {name}")
        else:
            print(f"  = place exists: {name}")

        rating = PlaceRating(
            user_id=user.user_id,
            place_id=place.place_id,
            rating=score,
        )
        db.add(rating)
        print(f"  + rating: {name} = {score}")

    for title, days_ago, final_rating, place_names in OUTINGS:
        existing = db.scalar(
            select(Outing).where(
                Outing.creator_id == user.user_id,
                Outing.title == title,
            )
        )
        if existing is not None:
            print(f"  = outing exists: {title}")
            continue

        completed_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        outing = Outing(
            creator_id=user.user_id,
            title=title,
            status="completed",
            scheduled_for=completed_at,
            completed_at=completed_at,
            final_rating=final_rating,
        )
        db.add(outing)
        db.flush()

        equal_weight = 1.0 / len(place_names)
        for position, p_name in enumerate(place_names, start=1):
            place = db.scalar(select(Place).where(Place.name == p_name))
            if place is None:
                print(f"  ! missing place for outing event: {p_name}")
                continue
            event = Event(
                creator_id=user.user_id,
                place_id=place.place_id,
                outing_id=outing.outing_id,
                sequence_position=position,
                status="completed",
                scheduled_for=completed_at,
                completed_at=completed_at,
                weight=equal_weight,
            )
            db.add(event)

        print(f"  + outing: {title} = {final_rating} ({len(place_names)} stops)")

    for name in SAVES:
        place = db.scalar(select(Place).where(Place.name == name))
        if place is None:
            print(f"  ! missing place for save: {name}")
            continue
        existing_save = db.scalar(
            select(SavedPlace).where(
                SavedPlace.user_id == user.user_id,
                SavedPlace.place_id == place.place_id,
            )
        )
        if existing_save is not None:
            print(f"  = save exists: {name}")
            continue
        db.add(SavedPlace(user_id=user.user_id, place_id=place.place_id))
        print(f"  + save: {name}")

    db.commit()
    print("Done.")


if __name__ == "__main__":
    main()
