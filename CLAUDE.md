# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TypeA** — social planner iOS app that predicts how much you'll enjoy an outing based on past ratings. Closed-loop feedback: predict → commit → rate → learn → better prediction.

Two ML systems:
- **Atomic Recommender:** Ridge regression predicting individual event ratings (1-10) with confidence intervals
- **Attribution Model:** Hierarchical regression decomposing multi-stop outing ratings into per-place contributions

## Domain Vocabulary (read this first)

- **Event** — atomic unit. One place + one time + one set of people. Most events are standalone (`outing_id = NULL`). Schema table: `events`.
- **Outing** — optional grouping of multiple events into a single occasion (a Friday night, a Saturday day-trip, a birthday). Has its own composite rating. Schema table: `outings`.
- **Stop** — UI/copy word for an event when it appears as part of an outing's sequence. Not a schema name. Used in button text like "+ Add another stop."
- **Plan / Planning** — verb only. Users *plan* events. The iOS tab is called "Plan." Never used as a noun in this codebase.

The composite entity is called `outing` rather than `night` because TypeA handles daytime sequences too. The atomic entity is called `event` rather than `plan` because `plan` is reserved for the verb.

## Repo Layout

The Python backend lives in `backend/`. The SwiftUI iOS client lives in `ios/TypeA/` (TYP-25 onward). Other top-level dirs (`eval/`, `fixtures/`, `coefficients/`, `plots/`) are placeholders for the ML pipeline. All backend commands below assume `cd backend` first. Long-form design docs live in `docs/`: `CURRENT_HANDOFF.md` is the living rolling doc (start here); per-ticket archaeology lives in `TYP_*_HANDOFF.md`; per-topic deep-dives in `JWT_AUTH_UNDERSTANDING.md`, `ML_RATING_UNDERSTANDING.md`, `TAB_SWITCHING_UNDERSTANDING.md`, `ALEMBIC_NOTES.md`, `RATING_ENDPOINTS.md`, `FRIENDSHIPS_ENDPOINTS.md`.

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

No test framework configured yet. Lint with `ruff check app/` from `backend/` (config in `backend/pyproject.toml`: rules `E, F, I, B, UP`, line-length 88, isort with `app` as first-party).

**Migration workflow:** Migration files in `backend/alembic/versions/` must be created via the alembic CLI — direct Write/Edit is blocked by a hook. Output the CLI command for the user to run; once the stub exists, you can edit its body.

## Architecture

Layered: **Route → Service → Repository → Database**. Auth is a FastAPI dependency, not a layer.

- `backend/app/main.py` — FastAPI entry point, CORS middleware, `/health` and `/` routes, registers routers
- `backend/app/auth.py` — `require_auth` dependency: validates Supabase JWT (ES256, JWKS-cached), provisions a `users` row on first sight (uses JWT `sub` as `user_id`)
- `backend/app/db.py` — SQLAlchemy engine + `get_db` session dependency
- `backend/app/routes/` — API endpoints (request handling only; depend on `require_auth` and `get_db`). One file per resource — note that `/saved_places` endpoints live in `routes/places.py` (no separate route file), though `repositories/saved_places.py` is its own module.
- `backend/app/services/` — business logic that orchestrates multiple repository calls or enforces cross-entity invariants (`events`, `outings`, `friendships`, `feed`, `event_invitations`, `outing_invitations`). Trivial single-call logic still lives directly in repositories.
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
event_invitations(user_id*, event_id*, rsvp_status, ics_sent_at?, created_at)    ← composite PK
outing_invitations(user_id*, outing_id*, rsvp_status, ics_sent_at?, created_at)  ← composite PK
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

Friend feed infrastructure (TYP-23 migration `fe0d54be86d0`):
- `place_ratings_user_created_idx` — composite `(user_id, created_at DESC)` for friend-feed rating reads
- `saved_places_user_created_idx` — composite `(user_id, created_at DESC)` for friend-feed save reads
- `outings_creator_completed_idx` — partial composite `(creator_id, completed_at DESC) WHERE status = 'completed' AND final_rating IS NOT NULL`; only indexes rows the feed actually reads

Invitation timestamps (TYP-20 migration `3067d8b0ab6b`):
- `event_invitations.created_at` and `outing_invitations.created_at` — `TIMESTAMPTZ NOT NULL DEFAULT now()`; backfilled at migration time so the `NOT NULL` is safe on existing rows. Powers the invitee's "invited X days ago" UX and is a candidate timestamp for surfacing invitations in `/me/feed` later.

## API Endpoints

Implemented:
- GET    /health                       → server status (no auth)
- GET    /me                           → current user (TYP-17, requires Bearer JWT)
- PATCH  /me                           → update display_name (TYP-17)
- GET    /places                       → fuzzy + radius search. Required `lat`, `lng`; optional `q` (when omitted, nearby-only mode — returns all places in radius ordered by distance, TYP-47); optional `radius_m` default 50000 max 100000. Returns `PlaceOut[]` with `category`, `distance_m`, and `is_saved` per result. `distance_m` is nullable on the schema (always populated when lat/lng supplied; null is reserved for the saved-places-without-caller-location case below). `category` was added to `PlaceOut` in TYP-60 to power the Profile Saved list's subtext (and is forward-useful for Search results).
- GET    /saved_places                 → user's bookmarks hydrated to places. Optional `lat`/`lng` (TYP-47): when supplied, returns `distance_m` per row and orders by distance ASC; when omitted, `distance_m` is null and rows are ordered alphabetically by name (Profile-tab use case — avoids forcing CoreLocation permission just to load a bookmark list).
- POST   /saved_places/{place_id}      → bookmark a place; idempotent via `ON CONFLICT DO NOTHING`; 404 if place missing (TYP-18) → 204
- DELETE /saved_places/{place_id}      → remove bookmark; idempotent (TYP-18) → 204
- POST/GET/PATCH/DELETE  /events, /events/{id}                          (TYP-19)
- POST   /events/{id}/confirm | /unconfirm | /cancel | /promote_to_outing (TYP-19; promote stubbed 501)
- POST   /outings                      → create outing with title (TYP-19)
- GET    /me/outings                   → user's outings, ordered by scheduled_for DESC NULLS LAST (TYP-19)
- GET    /outings/{id}                 → outing with embedded events (TYP-19)
- PATCH  /outings/{id}                 → edit title (TYP-19)
- DELETE /outings/{id}                 → 204; edit-gate; FK cascade behavior open (TYP-19)
- POST   /outings/{id}/confirm | /unconfirm | /cancel                   (TYP-19, cascades to events)
- POST   /place_ratings                → rate a place (0.0-10.0); always inserts new row (TYP-21)
- GET    /me/place_ratings             → user's ratings, deduped to latest-per-place via DISTINCT ON, sorted rating DESC (TYP-21)
- GET    /places/{place_id}/my_rating  → latest rating user has given this place; returns null if none (TYP-21)
- POST   /outings/{id}/rate            → write final_rating + per-event weight; cascades outing+events to completed (TYP-21)
- POST   /friends/requests                          → send a friend request; idempotent on existing pending/accepted; auto-accepts if reverse pending exists; 422 on self-friend (TYP-22)
- POST   /friends/requests/{user_id}/accept         → accept incoming request; mutates pending row + inserts mirror in one transaction (TYP-22)
- POST   /friends/requests/{user_id}/reject         → 204; hard-deletes the pending row (TYP-22)
- DELETE /me/friends/{user_id}                      → 204; deletes both rows in one OR-filter delete; 404 if not friends (TYP-22)
- GET    /me/friends                                → hydrated list (user_id, display_name, created_at) of accepted friends (TYP-22)
- GET    /me/friend_requests                        → hydrated list of incoming pending requests (TYP-22)
- GET    /me/feed                                   → cursor-paginated merged timeline of friends' ratings (latest per place via DISTINCT ON), saves, and rated+completed outings; `?limit=20&before=<iso8601>`; returns discriminated `FeedRatingOut | FeedSaveOut | FeedOutingOut` items + `next_cursor` (TYP-23)
- POST   /events/{id}/invitations                   → creator-only bulk invite of friend user_ids; `ON CONFLICT DO NOTHING` idempotent; 422 on non-friends; returns hydrated `EventInvitationOut[]` with invitee display_name (TYP-20)
- PATCH  /events/{id}/invitations/me                → invitee RSVP (`pending|accepted|rejected`, `Literal`-validated); 404 if not invited (TYP-20)
- GET    /me/event_invitations                      → invitee's incoming list with embedded `EventOut`, inviter's display_name, and `created_at` for "invited X days ago" (TYP-20)
- POST   /outings/{id}/invitations                  → outing variant of the bulk invite, same gates (TYP-20)
- PATCH  /outings/{id}/invitations/me               → outing RSVP (TYP-20)
- GET    /me/outing_invitations                     → invitee's incoming outings with embedded `OutingOut` (which itself embeds events) (TYP-20)
- TYP-19 retrofit: event/outing creation now auto-inserts the creator into the relevant invitations table with `rsvp_status='accepted'` (idempotent via `ON CONFLICT DO NOTHING`)
- GET    /places/{place_id}/predict     → stub returns `{"score": 7.5, "model_version": "stub-v0"}`; auth required; 404 if place missing. To be replaced by ridge regression once iOS is shipping real ratings.
- GET    /outings/{outing_id}/predict   → stub returns `{"score": 7.5, "model_version": "stub-v0"}`; auth required; no ownership check (any user can see their predicted score for any outing); 404 if outing missing. To be replaced by attribution model later.

Planned:
- POST   /comparisons      → head-to-head ranking
- Real implementations of `/places/{id}/predict` (ridge regression) and `/outings/{id}/predict` (attribution model) — stubs ship now to unblock iOS UI; real models trained once rating data exists

## Stack

- **FastAPI** + Pydantic v2 + Uvicorn
- **SQLAlchemy 2.0** + **Alembic** + **psycopg 3** (`psycopg`/`psycopg-binary` pinned to `3.2.13` — earliest version with prebuilt wheels for Python 3.13; do not downgrade)
- **Python 3.13.5** pinned via `backend/.python-version` (also matches local dev). Required because newer Pythons (3.14+) don't yet have prebuilt wheels for `pydantic-core`/`psycopg-binary` and Render's free build environment can't compile from Rust source (read-only Cargo cache).
- **PostgreSQL** (`type_a_dev` on localhost:5432)
- **scikit-learn / statsmodels** for ML inference
- **Supabase** for auth (JWT issuance only — Supabase's Postgres is unused)
- **PyJWT** (`pyjwt[crypto]`) for server-side JWT validation
- **Google Places API** for place metadata

## Configuration

Environment variables in `backend/.env` (see `backend/.env.example`), loaded by `dotenv` in `app/main.py`:
- `DATABASE_URL` — required by `app/db.py`
- `SUPABASE_URL` — required by `app/auth.py` (used to build the JWKS URL)
- `SUPABASE_PUBLISHABLE_KEY` — Supabase's public/anon key, used as the `apikey` header on client-side auth calls (e.g., password sign-in to fetch a JWT). The server validates JWTs via JWKS, not this key.

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

- The names `events` and `outings` were chosen deliberately (not the scoping doc's original `plans` and `nights`). See the Domain Vocabulary section above before renaming.
- Friendship status values follow the same `pending | accepted | rejected` CHECK pattern as RSVP fields, but `'rejected'` is currently unused at the application layer (reject hard-deletes; the constraint accepts the value if a future change wants soft-reject without a migration).
- App-wide tab selection lives in `ios/TypeA/TypeA/TabSelectionStore.swift` — an `@Observable` class injected at the app root the same way as `AuthStore`. Any view can read `@Environment(TabSelectionStore.self)` and write `tabSelection.current = .search` to switch tabs. `MainTabView` binds it into `TabView(selection:)` for two-way sync with the bottom tab bar. Pattern documented in `docs/TAB_SWITCHING_UNDERSTANDING.md` (with a stadium scoreboard analogy for the learner). Reuse for any cross-view shared state (FriendsStore, FeedStore, etc.) before reaching for `@AppStorage` or singletons.
- `ios/TypeA/Local.xcconfig` is gitignored (each dev fills in their own copy) so the LAN IP used for local-simulator dev can't leak into the commit.
- The user is learning. When asked to build something, prefer Socratic teaching over copy-paste solutions.
- Always read files before re-explaining edits — Alan often makes changes in his IDE before asking follow-up questions.

### Completed tickets

Backend:
- **TYP-8** — initial schema
- **TYP-16** — model tweaks + migration
- **TYP-17** — auth foundation: `/me` endpoints, Supabase JWT validation
- **TYP-18** — places discovery + bookmarking: `/places` search, `/saved_places` CRUD, earthdistance + pg_trgm indexes
- **TYP-19** — events + outings: 16 endpoints across atomic events and multi-stop outings, full lifecycle with confirm/unconfirm/cancel cascades
- **TYP-20** — invitations: 6 endpoints, bulk invite by friend user_ids with creator-only edit-gate + friendship-gate, idempotent `ON CONFLICT DO NOTHING`, `/me`-scoped RSVP path, embedded event/outing on incoming list, creator auto-RSVP retrofit on TYP-19 create routes; `created_at` column added to both invitation tables in migration `3067d8b0ab6b`; ICS punted to iOS EventKit, magic links punted to a separate sub-ticket
- **TYP-21** — ratings: 4 endpoints, `place_ratings` append-only with DISTINCT ON dedupe, `outings/{id}/rate` with per-event weights cascading to completed
- **TYP-22** — friendships: 6 endpoints, Option A schema = 1 row pending / 2 rows accepted, hard-delete reject, auto-accept on mutual pending, idempotent dup POST, OR-filter unfriend deletes both rows atomically
- **TYP-41** — `bio TEXT NULL` on users, `UserOut`/`UserUpdate` exposes the field, server-side 160-char cap via `Field(max_length=160)` (merged 2026-05-15 PR #27, bundled with TYP-61 — see `docs/TYP_61_HANDOFF.md`)
- **TYP-47** — optional `q` on `/places`, optional `lat`/`lng` on `/saved_places` (merged 2026-05-14 PR #25)
- **TYP-63** — README cleanup (merged 2026-05-12 PR #23)

iOS:
- **TYP-25** — project scaffold + APIClient singleton at https://type-a-api.onrender.com + KeychainStore + Models
- **TYP-26** — login + signup via Supabase, `AuthStore` `@Observable` + auth gating in `RootView`
- **TYP-10** — 4-tab SwiftUI shell with placeholder views
- **TYP-38** — Profile tab shell: empty state + CTA tab switching (merged 2026-05-11)
- **TYP-58** — Profile Places list (merged 2026-05-12 PR #22)
- **TYP-59** — Profile Outings list (merged 2026-05-13 PR #24)
- **TYP-60** — Profile Saved list (merged 2026-05-15 PR #26 — see `docs/TYP_60_HANDOFF.md`)
- **TYP-61** — Profile settings screen (push-navigation from gear icon, row-style edit pattern with single-field edit sheets, two-stage save flow, logout moved here from Profile; drive-by `APIClient` fix for Postgres microsecond timestamps that broke strict `.iso8601` parsing) — merged 2026-05-15 PR #27, bundled with TYP-41 — see `docs/TYP_61_HANDOFF.md`

Check `backend/app/models/` and `backend/alembic/versions/` for current schema state.

### Queued / blocked

- **TYP-49** (iOS Place detail screen) — next up; tapping a place row anywhere (Search/Profile/Feed) lands here
- **TYP-62** (real friends count on Profile) — blocked on TYP-43
- **TYP-64** (extract `ScorePill` + `CategoryIcon` into reusable components) — cleanup, queued for when a third consumer (Feed or Search tab) needs them
