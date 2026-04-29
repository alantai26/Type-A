# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Type A** — social planner iOS app that predicts how much you'll enjoy an outing based on past ratings. Closed-loop feedback: predict → commit → rate → learn → better prediction.

Two ML systems:
- **Atomic Recommender:** Ridge regression predicting individual event ratings (1-10) with confidence intervals
- **Attribution Model:** Hierarchical regression decomposing multi-stop outing ratings into per-place contributions

## Domain Vocabulary (read this first)

- **Event** — atomic unit. One place + one time + one set of people. Most events are standalone (`outing_id = NULL`). Schema table: `events`.
- **Outing** — optional grouping of multiple events into a single occasion (a Friday night, a Saturday day-trip, a birthday). Has its own composite rating. Schema table: `outings`.
- **Stop** — UI/copy word for an event when it appears as part of an outing's sequence. Not a schema name. Used in button text like "+ Add another stop."
- **Plan / Planning** — verb only. Users *plan* events. The iOS tab is called "Plan." Never used as a noun in this codebase.

The composite entity is called `outing` rather than `night` because Type A handles daytime sequences too. The atomic entity is called `event` rather than `plan` because `plan` is reserved for the verb.

## Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # localhost:8000, docs at /docs
alembic upgrade head                       # run migrations
alembic revision --autogenerate -m "msg"   # create migration after model changes
```

No test framework or linter configured yet.

## Architecture

Layered: **Route → Service → Repository → Database**

- `app/main.py` — FastAPI entry point, CORS middleware, root routes
- `app/routes/` — API endpoint definitions (request handling only)
- `app/services/` — Business logic
- `app/repositories/` — Data access layer
- `app/models/` — SQLAlchemy ORM models + Pydantic schemas

## Data Model (planned for TYP-8 — not yet implemented)
- users(id, email, display_name, created_at)
- places(id, name, lat, lng, category, source_url, google_place_id)
- saved_places(user_id, place_id, saved_at)
- events(id, creator_id, place_id, status, scheduled_for, completed_at,
- outing_id, sequence_position, final_rating, derived_score)
- outings(id, creator_id, status, scheduled_for, completed_at, final_rating, derived_score)
- event_invitations(event_id, invitee_user_id, rsvp_status, ics_sent_at)
- comparisons(user_id, item_a_id, item_b_id, item_type, winner_id, created_at)
- item_type: 'event' | 'outing'
- friendships(user_a, user_b, status, created_at)
- attribution_outputs(user_id, place_id, attributed_effect, confidence_lower, confidence_upper, model_version, computed_at)

Key design: events are atomic, outings are optional multi-stop groupings, comparisons are polymorphic (events or outings).

## Planned API Endpoints
- GET    /health           → server status
- GET    /events           → list events
- POST   /events           → create event
- GET    /events/{id}      → get event
- PATCH  /events/{id}      → update event
- DELETE /events/{id}      → delete event
- GET    /outings/{id}     → get outing with its events
- POST   /outings          → create outing (or convert events)
- GET    /predict_event    → ML prediction (atomic recommender)
- GET    /predict_outing   → ML prediction with per-event breakdown (attribution model)
- POST   /comparisons      → head-to-head ranking

## Stack

- **FastAPI** + Pydantic v2 + Uvicorn
- **SQLAlchemy 2.0** + **Alembic** + **psycopg 3**
- **PostgreSQL** (`type_a_dev` on localhost:5432)
- **scikit-learn / statsmodels** for ML inference
- **Supabase or Clerk** for auth (planned)
- **Google Places API** for place metadata

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DATABASE_URL`
- `SECRET_KEY`
- `SUPABASE_URL` / `SUPABASE_KEY`

## Git Workflow

Branches: `main` → `dev` (active development) → `prod` (release snapshots). Feature branches off `dev`, named like `TYP-8-database-schema`. PRs target `dev`. Commit messages prefixed with ticket ID (e.g. `TYP-8: ...`), include `Fixes TYP-X` to auto-close Linear tickets.

## Notes for Future Claude

- The names `events` and `outings` were chosen deliberately (not the scoping doc's original `plans` and `nights`). Don't rename without reading the design rationale in HANDOFF.md.
- TYP-8 is in progress, not complete. The data model above is planned, not yet in SQLAlchemy. Check `app/models/` to see actual current state.
- The user is learning. When asked to build something, prefer Socratic teaching over copy-paste solutions.