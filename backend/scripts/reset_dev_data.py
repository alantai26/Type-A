"""Wipe seeded dev data so the seed scripts can rebuild it cleanly (TYP-70).

Why this exists: `place_ratings` is append-only per TYP-21, so re-running a seed
script inserts duplicate ratings rather than updating them. After a couple of
runs the training set is silently double-weighted on the re-seeded rows. Rather
than dedupe forever downstream, reset and reseed.

What it deletes: all seeded *content* (places, ratings, saves, events, outings,
invitations) plus the synthetic `@synthetic.typea.dev` persona users.

What it KEEPS: real user rows. Their `user_id` values were issued by Supabase
and are referenced by live JWTs — `seed_dev_data.py` looks the real user up by
email and exits if it's missing, so deleting it would break reseeding until you
re-logged-in on iOS.

Usage:
    cd backend && source venv/bin/activate
    python scripts/reset_dev_data.py [--yes]

Then reseed:
    python scripts/seed_dev_data.py
    python scripts/seed_ml_data.py
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import delete, func, select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models.attribution_outputs import AttributionOutput  # noqa: E402
from app.models.comparisons import Comparison  # noqa: E402
from app.models.event_invitations import EventInvitation  # noqa: E402
from app.models.events import Event  # noqa: E402
from app.models.outing_invitations import OutingInvitation  # noqa: E402
from app.models.outings import Outing  # noqa: E402
from app.models.place_ratings import PlaceRating  # noqa: E402
from app.models.places import Place  # noqa: E402
from app.models.saved_places import SavedPlace  # noqa: E402
from app.models.users import User  # noqa: E402

SYNTHETIC_EMAIL_SUFFIX = "@synthetic.typea.dev"

# Children before parents — a FK violation here means a table was added to the
# schema without being added to this list.
DELETE_ORDER = [
    PlaceRating,
    SavedPlace,
    AttributionOutput,
    Comparison,
    EventInvitation,
    Event,
    OutingInvitation,
    Outing,
    Place,
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yes", action="store_true", help="skip the confirmation prompt"
    )
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL", "")
    host = urlparse(db_url.replace("+psycopg", "")).hostname or "?"
    print(f"DB host: {host}")
    if host not in ("localhost", "127.0.0.1"):
        print("Refusing to reset a non-local database.")
        sys.exit(1)

    db = SessionLocal()

    print("\nCurrent row counts:")
    for model in DELETE_ORDER:
        count = db.scalar(select(func.count()).select_from(model))
        print(f"  {model.__tablename__:22} {count}")

    synthetic = db.scalars(
        select(User).where(User.email.like(f"%{SYNTHETIC_EMAIL_SUFFIX}"))
    ).all()
    kept = db.scalars(
        select(User).where(~User.email.like(f"%{SYNTHETIC_EMAIL_SUFFIX}"))
    ).all()

    print(f"\nSynthetic users to delete ({len(synthetic)}):")
    for user in synthetic:
        print(f"  - {user.email}")
    print(f"\nReal users to KEEP ({len(kept)}):")
    for user in kept:
        print(f"  = {user.email} ({user.display_name})")

    if not args.yes:
        confirm = input("\nType 'reset' to proceed: ")
        if confirm.strip().lower() != "reset":
            print("Aborted.")
            sys.exit(0)

    print()
    for model in DELETE_ORDER:
        result = db.execute(delete(model))
        print(f"  - {result.rowcount:4} from {model.__tablename__}")

    if synthetic:
        result = db.execute(
            delete(User).where(User.email.like(f"%{SYNTHETIC_EMAIL_SUFFIX}"))
        )
        print(f"  - {result.rowcount:4} from users (synthetic only)")

    db.commit()
    print("\nDone. Reseed with:")
    print("  python scripts/seed_dev_data.py")
    print("  python scripts/seed_ml_data.py")


if __name__ == "__main__":
    main()
