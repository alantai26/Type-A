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

## Repo Layout

The Python backend lives in `backend/`. All commands below assume `cd backend` first. Other top-level dirs (`eval/`, `fixtures/`, `coefficients/`, `plots/`) are placeholders for the ML pipeline; `ios/` is reserved for the SwiftUI client (deferred — see MVP deadline note). Long-form design docs live in `docs/` (HANDOFF.md, JWT_AUTH_UNDERSTANDING.md, ML_RATING_UNDERSTANDING.md, ALEMBIC_NOTES.md).

## Commands

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # localhost:8000, docs at /docs
alembic upgrade head                       # apply migrations
alembic revision -m "msg"                  # create empty migration stub (then edit by hand)
alembic revision --autogenerate -m "msg"   # autogenerate from model diff
```

No test framework or linter configured yet.

**Migration workflow:** Migration files in `backend/alembic/versions/` must be created via the alembic CLI — direct Write/Edit is blocked by a hook. Output the CLI command for the user to run; once the stub exists, you can edit its body.

## Architecture

Layered: **Route → Service → Repository → Database**. Auth is a FastAPI dependency, not a layer.

- `backend/app/main.py` — FastAPI entry point, CORS middleware, `/health` and `/` routes, registers routers
- `backend/app/auth.py` — `require_auth` dependency: validates Supabase JWT (ES256, JWKS-cached), provisions a `users` row on first sight (uses JWT `sub` as `user_id`)
- `backend/app/db.py` — SQLAlchemy engine + `get_db` session dependency
- `backend/app/routes/` — API endpoints (request handling only; depend on `require_auth` and `get_db`)
- `backend/app/services/` — business logic (currently empty; logic that's just one DB call lives directly in repositories)
- `backend/app/repositories/` — data access layer
- `backend/app/models/` — SQLAlchemy ORM models only
- `backend/app/schemas/` — Pydantic request/response schemas (one file per resource: `users.py`, `places.py`, etc.)

## Data Model (TYP-8 — implemented, migrated)

```
users(user_id, email, display_name, created_at)
places(place_id, name, latitude, longitude, category, source_url, google_place_id)
saved_places(user_id*, place_id*)                                    ← composite PK
place_ratings(rating_id, user_id, place_id, rating, created_at)      ← multiple ratings per user/place
outings(outing_id, creator_id, title, status, scheduled_for?, completed_at?, final_rating?, derived_score?)
events(event_id, creator_id, place_id?, custom_location_name?, outing_id?, sequence_position?, status, scheduled_for?, completed_at?, weight?)
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

Place search infrastructure (TYP-18 migration `015dcc40c7ef`):
- Postgres extensions enabled: `cube`, `earthdistance` (radius queries), `pg_trgm` (fuzzy text)
- `places_earth_idx` — GiST on `ll_to_earth(latitude, longitude)` for distance prefilter
- `places_name_trgm_idx` — GIN trigram on `name` for `ILIKE`/similarity queries
- Search SQL lives in `app/repositories/places.py` and `app/repositories/saved_places.py` as raw `text()` because the earthdistance functions aren't first-class in SQLAlchemy ORM

## API Endpoints

Implemented:
- GET    /health                       → server status (no auth)
- GET    /me                           → current user (TYP-17, requires Bearer JWT)
- PATCH  /me                           → update display_name (TYP-17)
- GET    /places                       → fuzzy + radius search (TYP-18: required `q`, `lat`, `lng`; optional `radius_m` default 50000, max 100000). Returns `PlaceOut[]` with `distance_m` and `is_saved` per result.
- GET    /saved_places                 → user's bookmarks hydrated to places + distance from supplied `lat`/`lng` (TYP-18)
- POST   /saved_places/{place_id}      → bookmark a place; idempotent via `ON CONFLICT DO NOTHING`; 404 if place missing (TYP-18) → 204
- DELETE /saved_places/{place_id}      → remove bookmark; idempotent (TYP-18) → 204

Planned:
- GET/POST/GET/PATCH/DELETE  /events, /events/{id}
- GET    /outings/{id}     → outing with its events
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

Environment variables in `backend/.env` (see `backend/.env.example`), loaded by `dotenv` in `app/main.py`:
- `DATABASE_URL` — required by `app/db.py`
- `SUPABASE_URL` — required by `app/auth.py` (used to build the JWKS URL)
- `SUPABASE_KEY` — for client-side issuance (server validates via JWKS, not this key)

Auth flow: clients send `Authorization: Bearer <supabase_jwt>`. The server fetches Supabase's JWKS, verifies ES256 signatures, and trusts the `sub`/`email` claims. First-time `sub` UUIDs are auto-provisioned into `users`.

## Git Workflow

Branches: `main` → `dev` (active development) → `prod` (release snapshots). Feature branches off `dev`, named like `TYP-8-database-schema`. PRs target `dev`. Commit messages prefixed with ticket ID (e.g. `TYP-8: ...`), include `Fixes TYP-X` to auto-close Linear tickets.

## Claude Code Hooks

Six hooks configured in `.claude/settings.json` (project root):

- **`protect-files.sh`** (PreToolUse: Edit|Write) — blocks edits to `.env`, `.git/`, credentials, keys
- **`block-direct-migration-write.sh`** (PreToolUse: Edit|Write) — blocks Edit/Write to `alembic/versions/`; use the alembic CLI to generate the stub first
- **`block-dangerous.sh`** (PreToolUse: Bash) — blocks `rm -rf`, `DROP`, force push, `git reset --hard`
- **`block-direct-db.sh`** (PreToolUse: Bash) — blocks raw SQL writes via psql (SELECT/inspect allowed)
- **`block-schema-drift.sh`** (Stop) — blocks if models changed without an Alembic migration
- **`auto-update-docs.sh`** (Stop) — blocks if significant code changed without CLAUDE.md/README update

## Notes for Future Claude

- The names `events` and `outings` were chosen deliberately (not the scoping doc's original `plans` and `nights`). Don't rename without reading the design rationale in `docs/HANDOFF.md`.
- TYP-8 (schema), TYP-16 (model tweaks + migration), TYP-17 (auth foundation: `/me` endpoints, Supabase JWT validation), and TYP-18 (places discovery + bookmarking: `/places` search, `/saved_places` CRUD, earthdistance + pg_trgm indexes) are complete. Check `backend/app/models/` and `backend/alembic/versions/` for current state.
- The user is learning. When asked to build something, prefer Socratic teaching over copy-paste solutions.
- Always read files before re-explaining edits — Alan often makes changes in his IDE before asking follow-up questions.