# TypeA

The social planner that learns what makes a great outing for you, then predicts how the next one will go before you commit.

## What It Is

An iOS app built around **events** — a single place + time + people unit (e.g. "Top Golf, Friday 6pm, with Oscar and Jack"). Events are atomic by default, because that matches how people actually think: "let's go to the movies," not "let's go to the movies, then bowling, then dessert."

Some occasions *are* multi-stop — birthdays, special occasions, a real Friday night out, a Saturday brunch + bookstore + coffee. For those, events can be optionally grouped into an **outing**. The outing gets its own composite rating that the ML model decomposes into per-event contributions.

### Naming rationale

The composite entity is called an `outing` rather than a `night` because TypeA handles daytime sequences (brunch → hike → dinner) just as much as evening ones. The atomic entity is called an `event` rather than a `plan` because "plan" is reserved for the verb in product UI ("to plan an event"). In grouped UI copy, an event in a sequence is referred to as a "stop" — that's a role word, not a schema name.

## Two ML Systems

- **Atomic recommender** — predicts how much you'll like any individual event (place + companions + day/time)
- **Attribution model** — decomposes outing ratings into per-place, per-companion contributions

Past ratings train both models. Future events surface predicted scores in the planning UI. Events become calendar invites.

## Tech Stack

**Frontend:** iOS / SwiftUI, MapKit, CoreLocation (read-only in v1)
**Backend:** FastAPI, SQLAlchemy + Alembic, PostgreSQL
**ML:** scikit-learn / statsmodels, Jupyter notebooks, FastAPI inference endpoints
**Auth & Hosting:** Supabase or Clerk, Fly.io or Railway, managed Postgres
**Other:** `.ics` via Resend/SendGrid, Google Places API, APNs via OneSignal/Firebase

## Key Design Decisions

1. **Two tables: events and outings.** Most events are atomic (`outing_id = NULL`). Two tables instead of one because the attribution ML model trains on a separate entity with its own composite rating, which can't live cleanly on the events table.
2. **Two-tier ML.** Atomic recommender works from day one. Attribution model kicks in once users log multi-stop outings.
3. **Closed-loop feedback.** Rating an event makes the planner smarter.
4. **Synthetic data for week 1–3.** Real data from alpha cohort validates models in week 4.

## Getting Started

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your Postgres credentials
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Server: `http://localhost:8000`. Docs: `/docs`.

## What's Deferred to v2

Per-friend predicted scores, CoreLocation auto-inference, sequence-aware ML, standalone map tab, calendar conflict detection, cost splitting, reservation booking, restaurants/food.

## Branch Strategy

- `main` — bootstrap state
- `dev` — active development
- `prod` — weekly release snapshots from dev

All code through PRs to `dev`.
