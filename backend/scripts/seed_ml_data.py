"""
Synthetic ML training data (TYP-69).

Hand-curated PREFERENCE_MATRIX + PLACES are the "ground truth" the mvML
models should recover in TYP-70 / TYP-71. Ratings are sampled uniformly
within each user's per-category range; outings mix a top-preferred stop
(weight 0.7) with a bottom-preferred stop (weight 0.3) so the attribution
model has a real signal to fit.

Usage:
    cd backend && source venv/bin/activate
    python scripts/seed_ml_data.py [--seed 42] [--coverage 0.85] [--outings-per-user 5]

Idempotent: re-running skips existing users/places/outings; ratings still
append (per TYP-21). Use --seed for reproducible sampling.
"""

import argparse
import os
import random
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.db import SessionLocal  # noqa: E402
from scripts.seed_dev_data import (  # noqa: E402
    create_outing_with_stops,
    create_place,
    create_rating,
    create_user,
)

CATEGORIES = ["Activity", "Restaurant", "Cafe", "Dessert", "Bar"]

# The "answer key" — TYP-70's eval script recovers these midpoints.
# Kept as a wide table for readability; noqa'd on line-length.
# fmt: off
PREFERENCE_MATRIX: dict[str, dict[str, tuple[float, float]]] = {
    "activity_fan":   {"Activity": (8, 10), "Restaurant": (4, 6),  "Cafe": (4, 6),  "Dessert": (5, 7),  "Bar": (5, 7)},   # noqa: E501
    "foodie":         {"Activity": (3, 5),  "Restaurant": (8, 10), "Cafe": (7, 9),  "Dessert": (7, 9),  "Bar": (5, 7)},   # noqa: E501
    "coffee_snob":    {"Activity": (3, 5),  "Restaurant": (5, 7),  "Cafe": (9, 10), "Dessert": (6, 8),  "Bar": (4, 6)},   # noqa: E501
    "bar_hopper":     {"Activity": (5, 7),  "Restaurant": (6, 8),  "Cafe": (4, 6),  "Dessert": (5, 7),  "Bar": (8, 10)},  # noqa: E501
    "dessert_head":   {"Activity": (4, 6),  "Restaurant": (6, 8),  "Cafe": (6, 8),  "Dessert": (9, 10), "Bar": (4, 6)},   # noqa: E501
    "omnivore":       {"Activity": (6, 8),  "Restaurant": (6, 8),  "Cafe": (6, 8),  "Dessert": (6, 8),  "Bar": (6, 8)},   # noqa: E501
    "hater":          {"Activity": (2, 4),  "Restaurant": (2, 4),  "Cafe": (2, 4),  "Dessert": (2, 4),  "Bar": (2, 4)},   # noqa: E501
    "chill_balanced": {"Activity": (6, 8),  "Restaurant": (7, 9),  "Cafe": (7, 9),  "Dessert": (6, 8),  "Bar": (5, 7)},   # noqa: E501
}
# fmt: on

# 10 per category. Count matters more than identity here: each persona rates
# each place at most once, so observations-per-cell is capped at
# (places in that category) × coverage. At 5 places/category the model was
# fitting each of the 40 cells on ~4 ratings; 10 doubles that.
PLACES: list[tuple[str, str, float, float]] = [
    # Activity
    ("TopGolf Canton",              "Activity",   42.155, -71.147),
    ("Kings Back Bay",              "Activity",   42.348, -71.079),
    ("F1 Arcade Seaport",           "Activity",   42.352, -71.048),
    ("Charles River Canoe & Kayak", "Activity",   42.365, -71.107),
    ("Puttshack Fenway",            "Activity",   42.348, -71.100),
    ("Lucky Strike Fenway",         "Activity",   42.347, -71.098),
    ("Boston Bowl",                 "Activity",   42.291, -71.055),
    ("Museum of Science",           "Activity",   42.367, -71.071),
    ("New England Aquarium",        "Activity",   42.359, -71.049),
    ("Time Out Market",             "Activity",   42.348, -71.103),
    # Restaurant
    ("Yume Ga Arukara",             "Restaurant", 42.389, -71.119),
    ("Pho Basil",                   "Restaurant", 42.348, -71.084),
    ("Matsunori Handroll Bar",      "Restaurant", 42.352, -71.068),
    ("Mooo",                        "Restaurant", 42.359, -71.061),
    ("Saigon Fusion",               "Restaurant", 42.345, -71.082),
    ("Giulia",                      "Restaurant", 42.376, -71.117),
    ("Toro",                        "Restaurant", 42.342, -71.075),
    ("Neptune Oyster",              "Restaurant", 42.363, -71.055),
    ("Sarma",                       "Restaurant", 42.396, -71.096),
    ("Krasi",                       "Restaurant", 42.351, -71.078),
    # Cafe
    ("Tatte Bakery",                "Cafe",       42.358, -71.068),
    ("HeyTea",                      "Cafe",       42.349, -71.082),
    ("Molly Tea",                   "Cafe",       42.347, -71.086),
    ("Teazi",                       "Cafe",       42.348, -71.084),
    ("Blank Street Coffee",         "Cafe",       42.354, -71.070),
    ("Thinking Cup",                "Cafe",       42.352, -71.063),
    ("Pavement Coffeehouse",        "Cafe",       42.348, -71.088),
    ("George Howell Coffee",        "Cafe",       42.352, -71.055),
    ("Gracenote Coffee",            "Cafe",       42.349, -71.058),
    ("Render Coffee",               "Cafe",       42.341, -71.071),
    # Dessert
    ("Oasis",                       "Dessert",    42.350, -71.062),
    ("Berryline",                   "Dessert",    42.373, -71.121),
    ("Meetfresh",                   "Dessert",    42.351, -71.063),
    ("Matcha Miako",                "Dessert",    42.349, -71.083),
    ("Davinci Gelato",              "Dessert",    42.350, -71.062),
    ("Mike's Pastry",               "Dessert",    42.363, -71.054),
    ("Modern Pastry",               "Dessert",    42.363, -71.056),
    ("J.P. Licks",                  "Dessert",    42.348, -71.087),
    ("Toscanini's",                 "Dessert",    42.365, -71.104),
    ("Christina's Ice Cream",       "Dessert",    42.373, -71.107),
    # Bar
    ("Drink",                       "Bar",        42.352, -71.048),
    ("Wink & Nod",                  "Bar",        42.348, -71.083),
    ("Yvonne's",                    "Bar",        42.356, -71.061),
    ("The Hawthorne",               "Bar",        42.348, -71.098),
    ("Backbar",                     "Bar",        42.395, -71.099),
    ("Bleacher Bar",                "Bar",        42.346, -71.097),
    ("Lolita Cocina",               "Bar",        42.351, -71.073),
    ("Shore Leave",                 "Bar",        42.343, -71.072),
    ("Havana Club",                 "Bar",        42.365, -71.103),
    ("The Automatic",               "Bar",        42.365, -71.100),
]


def user_email(key: str) -> str:
    return f"{key}@synthetic.typea.dev"


def user_display(key: str) -> str:
    return key.replace("_", " ").title()


def sample_rating(user_key: str, category: str) -> float:
    low, high = PREFERENCE_MATRIX[user_key][category]
    return round(random.uniform(low, high), 1)


def generate_ratings(db, users, places, coverage: float) -> int:
    count = 0
    for key, user in users.items():
        for name, cat, _, _ in PLACES:
            if random.random() > coverage:
                continue
            rating = sample_rating(key, cat)
            create_rating(db, user.user_id, places[name].place_id, rating)
            count += 1
    return count


def generate_outings(db, users, places, per_user: int) -> int:
    places_by_cat = {c: [p[0] for p in PLACES if p[1] == c] for c in CATEGORIES}
    count = 0
    for key, user in users.items():
        prefs = PREFERENCE_MATRIX[key]
        ranked = sorted(prefs.items(), key=lambda kv: -(kv[1][0] + kv[1][1]) / 2)
        top_cats = [c for c, _ in ranked[:2]]
        bot_cats = [c for c, _ in ranked[-2:]]

        for i in range(per_user):
            top_cat = top_cats[i % len(top_cats)]
            bot_cat = bot_cats[i % len(bot_cats)]
            top_name = random.choice(places_by_cat[top_cat])
            bot_name = random.choice(places_by_cat[bot_cat])

            weights = (0.7, 0.3)
            final_rating = round(
                weights[0] * sample_rating(key, top_cat)
                + weights[1] * sample_rating(key, bot_cat),
                1,
            )
            title = f"{key} outing {i + 1}"
            create_outing_with_stops(
                db,
                creator_id=user.user_id,
                title=title,
                stops=[
                    (places[top_name].place_id, weights[0]),
                    (places[bot_name].place_id, weights[1]),
                ],
                final_rating=final_rating,
            )
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--coverage", type=float, default=0.85)
    parser.add_argument("--outings-per-user", type=int, default=5)
    args = parser.parse_args()

    random.seed(args.seed)

    db_url = os.getenv("DATABASE_URL", "")
    host = urlparse(db_url.replace("+psycopg", "")).hostname or "?"
    print(f"DB host: {host}")
    if host not in ("localhost", "127.0.0.1"):
        confirm = input("Non-local DB. Type 'yes' to proceed: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    db = SessionLocal()

    print(f"Seeding {len(PREFERENCE_MATRIX)} synthetic users...")
    users = {
        key: create_user(db, user_email(key), user_display(key))
        for key in PREFERENCE_MATRIX
    }

    print(f"Seeding {len(PLACES)} places...")
    places = {
        name: create_place(db, name, cat, lat, lng)
        for name, cat, lat, lng in PLACES
    }

    print(f"Generating ratings (coverage={args.coverage})...")
    n_ratings = generate_ratings(db, users, places, args.coverage)

    print(f"Generating outings ({args.outings_per_user}/user)...")
    n_outings = generate_outings(db, users, places, args.outings_per_user)

    db.commit()
    print(f"Done. Ratings: {n_ratings}, Outings: {n_outings}.")


if __name__ == "__main__":
    main()
