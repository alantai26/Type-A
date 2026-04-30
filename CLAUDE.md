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

## Data Model (TYP-8 — implemented, migrated)

```
users(user_id, email, display_name, created_at)
places(place_id, name, latitude, longitude, category, source_url, google_place_id)
saved_places(user_id*, place_id*)                                    ← composite PK
place_ratings(rating_id, user_id, place_id, rating, created_at)      ← multiple ratings per user/place
outings(outing_id, creator_id, status, scheduled_for, completed_at, final_rating, derived_score)
events(event_id, creator_id, place_id?, custom_location_name?, outing_id?, sequence_position?, status, scheduled_for, completed_at?, weight?)
event_invitations(user_id*, event_id*, rsvp_status, ics_sent_at?)    ← composite PK
outing_invitations(user_id*, outing_id*, rsvp_status, ics_sent_at?)  ← composite PK
friendships(user_a_id*, user_b_id*, status, created_at)              ← composite PK, two rows per friendship
comparisons(comparison_id, user_id, item_a_id, item_b_id, item_type, winner_id, created_at)
attribution_outputs(attribution_id, user_id, place_id, attributed_effect, confidence_lower, confidence_upper, model_version, computed_at)
```

Key design:
- Events are atomic, outings are optional multi-stop groupings
- Comparisons are polymorphic: `item_type` is `'place' | 'outing'`, no FK on item_a/b/winner (can't FK to two tables)
- `place_id` on events is nullable — informal locations use `custom_location_name` instead (e.g. "Josh's House")
- Ratings live on `place_ratings` (per-place) and `outings.final_rating` (composite) — events are not rated directly
- `weight` on events stores optional stop weighting within an outing (0.0-1.0), used as ML training data
- Status fields enforced via CHECK constraints: `planning_in_progress | confirmed | completed | cancelled` (both outings and events)
- RSVP fields enforced via CHECK: `pending | accepted | rejected`
- All IDs are UUIDs, all timestamps are TIMESTAMPTZ

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
- **Supabase** for auth (JWT issuance only — Supabase's Postgres is unused)
- **PyJWT** (`pyjwt[crypto]`) for server-side JWT validation
- **Google Places API** for place metadata

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DATABASE_URL`
- `SECRET_KEY`
- `SUPABASE_URL` / `SUPABASE_KEY`

## Git Workflow

Branches: `main` → `dev` (active development) → `prod` (release snapshots). Feature branches off `dev`, named like `TYP-8-database-schema`. PRs target `dev`. Commit messages prefixed with ticket ID (e.g. `TYP-8: ...`), include `Fixes TYP-X` to auto-close Linear tickets.

## Claude Code Hooks

Five hooks configured in `.claude/settings.json` (project root):

- **`protect-files.sh`** (PreToolUse: Edit|Write) — blocks edits to `.env`, `.git/`, credentials, keys
- **`block-dangerous.sh`** (PreToolUse: Bash) — blocks `rm -rf`, `DROP`, force push, `git reset --hard`
- **`block-direct-db.sh`** (PreToolUse: Bash) — blocks raw SQL writes via psql (SELECT/inspect allowed)
- **`block-schema-drift.sh`** (Stop) — blocks if models changed without Alembic migration
- **`auto-update-docs.sh`** (Stop) — blocks if significant code changed without CLAUDE.md/README update

## Notes for Future Claude

- The names `events` and `outings` were chosen deliberately (not the scoping doc's original `plans` and `nights`). Don't rename without reading the design rationale in HANDOFF.md.
- TYP-8 is complete. All 11 SQLAlchemy models + initial migration are in place. Check `app/models/` for current state.
- The user is learning. When asked to build something, prefer Socratic teaching over copy-paste solutions.
- Always read files before re-explaining edits — Alan often makes changes in his IDE before asking follow-up questions.