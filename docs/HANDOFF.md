# Type A — Handoff Doc (TYP-8 Complete)

## For the next Claude reading this

Alan (NU CS '27) is building Type A, a social planner iOS app. Teach Socratically — push him to make decisions and defend them. Don't dump code; ask questions, let him own the design. He's fast, don't over-explain things he already knows. Always read files before re-explaining — he often edits in his IDE before asking follow-up questions.

---

## Current State

### Complete
- **TYP-5**: GitHub setup
- **TYP-6**: Requirements gathering
- **TYP-7**: Postgres + FastAPI skeleton (health endpoint, CORS, Swagger at /docs)
- **TYP-8**: Database schema — SQLAlchemy 2.0 models, Alembic init, initial migration applied

### Up Next: TYP-9
Likely CRUD endpoints for events/outings. Check Linear for the actual ticket.

---

## What Was Built in TYP-8

### Models (12 files in `app/models/`)
- `base.py` — DeclarativeBase
- `users.py` — User
- `places.py` — Place
- `saved_places.py` — SavedPlace (composite PK)
- `place_ratings.py` — PlaceRating (new — not in original spec)
- `outings.py` — Outing
- `events.py` — Event
- `event_invitations.py` — EventInvitation (composite PK)
- `outing_invitations.py` — OutingInvitation (composite PK)
- `friendships.py` — Friendship (composite PK)
- `comparisons.py` — Comparison (polymorphic, no FK on items)
- `attribution_outputs.py` — AttributionOutput
- `__init__.py` — imports all models (required for Alembic discovery)

### Alembic
- `alembic.ini` — configured with `postgresql+psycopg://` (psycopg v3 driver)
- `alembic/env.py` — imports from `app.models` (not `app.models.base`)
- Migration `40546b016600_initial_schema.py` — applied to `type_a_dev`

### Claude Code Hooks (`.claude/hooks/` at project root)
- `protect-files.sh` — blocks edits to .env, .git, credentials, keys
- `block-dangerous.sh` — blocks rm -rf, DROP, force push, etc.
- `block-direct-db.sh` — blocks raw SQL writes (psql INSERT/UPDATE/DELETE)
- `block-schema-drift.sh` — blocks if models changed without migration
- `auto-update-docs.sh` — blocks if code changed without doc updates

---

## Schema Changes from Original Spec

### 1. `place_ratings` table added (new)
Original spec had `final_rating` on events. Alan realized events are too granular for ratings — "TopGolf with Jake on Tuesday" isn't a useful thing to rate. Places are. Users rate **places**, and the companions are auto-populated from event data for the ML model. Multiple ratings per user per place allowed (rating over time).

### 2. `final_rating` and `derived_score` removed from events
Events are logs, not rated entities. Ratings live on `place_ratings` (per-place) and `outings.final_rating` (composite experience).

### 3. `weight` added to events
When a user rates an outing, they can optionally weight which stops made it better (slider UI, 0.0-1.0). This becomes training data for the attribution model. Default: equal weight across stops.

### 4. `custom_location_name` added to events
`place_id` is nullable — some stops are informal ("Josh's House") and shouldn't be in the public `places` table. `custom_location_name` is the fallback.

### 5. `outing_invitations` table added (not in original scoping doc)
Two invitation use cases: invite to a single event vs invite to a full outing. Separate tables, same structure, different FK targets.

### 6. Comparisons are `'place' | 'outing'` (was `'event' | 'outing'`)
Matches the rating change — you compare places head-to-head, not individual events.

### 7. Status enforced via CHECK constraints (not ENUMs)
Alan's professor advised against Postgres ENUMs. CHECK constraints chosen for simplicity — `ALTER TYPE` migrations are messy, CHECK swaps are clean.

### 8. Category on places is plain String
Considered lookup table, decided it's overkill for a small fixed set (food, activity, etc.).

---

## Rating & ML Flow (as designed)

### Place Rating (Atomic Recommender)
1. User completes an event (e.g., TopGolf with Jake)
2. App prompts: "Rate TopGolf" (the place, not the event)
3. Companions auto-populated from event invitations
4. Rating stored in `place_ratings`
5. ML uses place + companion data as features to predict future enjoyment

### Outing Rating (Attribution Model)
1. User completes an outing (e.g., TopGolf then Jake's house)
2. App prompts: "Rate the outing overall"
3. Optional: weight the stops via slider (which part made it better?)
4. `outings.final_rating` stores the composite score
5. `events.weight` stores per-stop weighting
6. Attribution model decomposes composite ratings into per-place effects over time
7. Future predictions: "Adding TopGolf to this outing would bump your predicted enjoyment by +2"

---

## Key Design Decisions (carried forward from schema session)

- All IDs are UUIDs (consistent with Supabase/Clerk auth)
- All timestamps are TIMESTAMPTZ (multi-timezone users)
- Ratings stored as FLOAT (validation in Pydantic, not DB)
- Friendships: two rows per friendship for query simplicity
- Comparisons: polymorphic, no FK enforcement (app layer validates)
- SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` syntax throughout

---

## Concepts Alan Has Solid Grasp On
- HTTP methods, REST, CRUD
- Pydantic validation, Swagger
- ORMs (used Prisma in StudyBuddies, now SQLAlchemy 2.0)
- Migrations as "git for the database"
- FK direction (child -> parent)
- Composite PKs
- Polymorphic relationships and why FKs can't enforce them
- 1:M vs M:M, when bridge tables are needed
- UUID vs integer PKs
- TIMESTAMP WITH TIME ZONE vs plain TIMESTAMP
- SQLAlchemy 2.0 Mapped[] declarative syntax
- Alembic autogenerate + upgrade workflow
- CHECK constraints vs ENUMs vs lookup tables
- Nullable via `Mapped[type | None]` (no need for `nullable=True`)

## Concepts NOT Yet Covered
- Indexing strategy (which columns to index beyond PKs/FKs)
- Relationships (SQLAlchemy `relationship()` for ORM navigation)
- Pydantic schemas (request/response models)
- Repository pattern implementation
- Database session management (async vs sync)
- Testing strategy

---

## Teaching Style Notes
- Alan responds well to single-select button questions
- Push him to defend decisions in interview-friendly soundbites
- He pushes back when something feels wrong — encourage it
- Cut trade-offs land well, pure best-practice lectures don't
- Always read files before explaining — he edits in IDE before asking
- Don't re-explain things he already fixed
