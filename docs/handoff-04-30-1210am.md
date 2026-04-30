# Handoff — 2026-04-30 ~12:10am (TYP-18 in progress)

Snapshot at the end of the TYP-18 build session. Code-complete on the ticket; not yet manually tested or committed.

---

## What's on the branch

Branch: `typ-18-places-discovery-bookmarking`

### Migration (already on branch from earlier in session)
`backend/alembic/versions/015dcc40c7ef_place_search_and_distance_indexes.py`
- Enables `cube`, `earthdistance`, `pg_trgm` Postgres extensions
- `places_earth_idx` — GiST on `ll_to_earth(latitude, longitude)` for fast radius prefilter
- `places_name_trgm_idx` — GIN trigram on `name` for fast `ILIKE`/similarity search

### New files this session
```
backend/app/schemas/__init__.py        (new directory, parallel to models/)
backend/app/schemas/users.py           (moved from models/user_schemas.py)
backend/app/schemas/places.py          (PlaceOut: place_id, name, lat, lng, distance_m, is_saved)
backend/app/repositories/places.py     (search_places: fuzzy + radius + is_saved)
backend/app/repositories/saved_places.py (list_saved, save, unsave)
backend/app/routes/places.py           (GET /places, GET/POST/DELETE /saved_places/...)
```

### Files modified
- `backend/app/main.py` — registers `places_routes.router`
- `backend/app/routes/users.py` — import path updated to `app.schemas.users`
- `CLAUDE.md` — Architecture (split models/schemas), Data Model (added "Place search infrastructure"), API Endpoints (4 new), "Notes for Future Claude" (TYP-18 marked done)
- `docs/JWT_AUTH_UNDERSTANDING.md` — `app/models/user_schemas.py` → `app/schemas/users.py`
- `docs/HANDOFF.md` — added "Informal-place ratings" subsection under Rating & ML Flow
- `.claude/hooks/block-schema-drift.sh` — Pydantic warning now only fires when a `tsconfig.json` exists

### Files deleted
- `backend/app/models/user_schemas.py` (moved)
- `backend/app/models/place_schemas.py` (moved)

---

## API surface added

| Method | Path | Required query | Returns | Notes |
|---|---|---|---|---|
| GET | `/places` | `q`, `lat`, `lng` (`radius_m` default 50000, max 100000) | `list[PlaceOut]` | Discovery search; `is_saved` per row |
| GET | `/saved_places` | `lat`, `lng` | `list[PlaceOut]` | User's bookmarks + distance |
| POST | `/saved_places/{place_id}` | — | 204 | 404 if place missing; idempotent via `ON CONFLICT DO NOTHING` |
| DELETE | `/saved_places/{place_id}` | — | 204 | Idempotent |

All four require Bearer JWT (`Depends(require_auth)`).

---

## Request flow (memorize this shape)

```
HTTP request
  → FastAPI route       (auth + Query validation + status codes)
    → Repository        (SQL, transactions)
      → Postgres
    ← list[dict]
  ← Pydantic schema     (validates + serializes JSON via response_model)
HTTP response
```

Walked through end-to-end with `GET /places?q=top&lat=42.34&lng=-71.10&radius_m=10000` during the session. Six steps:

1. **Auth dependency** — `require_auth` validates JWT against Supabase JWKS, returns User row (auto-provisions on first sight). 401 short-circuits the route.
2. **Query validation** — FastAPI's `Query(..., min_length=1, ge=-90, le=90, ...)` rejects malformed requests with 422 before route runs.
3. **DB session** — `get_db` yields a SQLAlchemy session, scoped per request, auto-closed.
4. **Route → Repository** — route does *nothing* but call the repo. Layer split: route = HTTP concerns; repo = SQL.
5. **The SQL** — single query does fuzzy search + distance filter + is_saved computation. Three patterns worth knowing (see below).
6. **Response shaping** — repo returns `list[dict]`; FastAPI validates each dict against `PlaceOut` per `response_model=list[PlaceOut]`; serializes to JSON.

---

## Key technical patterns introduced

### Two-stage distance filter
```sql
WHERE earth_box(ll_to_earth(:lat,:lng), :radius_m) @> ll_to_earth(p.latitude, p.longitude)  -- coarse, GiST-indexed
  AND earth_distance(...) < :radius_m                                                        -- precise, exact
```
`earth_box` uses the GiST index — eliminates 99% of rows fast. `earth_distance` runs only on survivors. Without the box prefilter, every query scans the full table.

### Trigram-accelerated `ILIKE`
`name ILIKE '%foo%'` is normally a sequential scan (B-tree can't help with leading `%`). The `pg_trgm` GIN index indexes every 3-char substring of every name and makes it fast.

### `is_saved` via LEFT JOIN (avoids N+1)
Naïve approach: search places, then per-row query saved_places to compute is_saved → N+1 problem. LEFT JOIN gets it in one query: `(sp.user_id IS NOT NULL) AS is_saved`.

### `ON CONFLICT DO NOTHING` for idempotent inserts
```python
insert(SavedPlace).values(...).on_conflict_do_nothing(index_elements=["user_id", "place_id"])
```
Without it, a second `POST /saved_places/{id}` would raise `IntegrityError` (composite PK violation) → FastAPI 500. With it, it's a clean no-op.

### Why raw SQL via `text()`
`earth_distance`, `earth_box`, `ll_to_earth` are PostgreSQL extension functions — SQLAlchemy ORM doesn't know about them. `text()` is the standard escape hatch. Bind params (`:lat`, `:user_id`) are still parameterized → no SQL-injection risk.

---

## Design decisions made this session

### 1. `q` always required on `/places`
Discussed allowing `q` to be optional ("nearby" mode). Decided against for simplicity. Always require.

### 2. `GET /saved_places` requires `lat`/`lng` (returns distance)
Beli-style: saved list shows distance from current location, not just name + saved date.

### 3. `is_saved` flag on search results
Each search result tells the client whether it's already bookmarked → iOS button can render correct state without N+1 fetches.

### 4. `category` excluded from `PlaceOut`
List view shows name + distance + actions only. Category is on the DB row but not exposed.

### 5. Schemas moved out of `models/` into their own directory
`backend/app/schemas/` now sits parallel to `models/`, `routes/`, `repositories/`. Files dropped the `_schemas` suffix since the directory name carries it.

### 6. No services layer for TYP-18
None of the four endpoints orchestrate across multiple repos. Even the POST (existence check + insert) is too thin to abstract. Convention from CLAUDE.md: services only when there's real cross-repo orchestration. Future tickets (POST /events, POST /place_ratings, POST /outings) will likely earn services.

### 7. Informal-place ratings = no schema change needed (logged in `docs/HANDOFF.md`)
Question raised: how do you rate a solo event at "Jim's house"? Answer: schema already prevents it. `place_ratings.place_id` is FK to `places`; informal locations live as `events.custom_location_name` strings with no `places` row, so they're physically un-rateable. Privacy is automatic. Open question deferred to whichever future ticket builds the rating prompt UI.

### 8. Schema-drift hook softened
The Stop hook used to block on every Pydantic change with "update TS types." Now it only fires when a `tsconfig.json` exists in the repo. iOS (Swift) and the bare backend phase are silent.

---

## What's NOT done — open before TYP-18 closes

1. **No data in `places` table.** All four endpoints will return `[]` until rows exist. Two paths:
   - Manual seed: 3-5 INSERT statements via psql (Boston-area coords) — fastest demo path
   - Google Places integration: probably its own follow-up ticket (TYP-19?), pulls real data on demand
2. **No manual end-to-end test.** Server hasn't been started; endpoints haven't been hit. Plan:
   - `cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload`
   - Get a JWT (Supabase signin)
   - `curl -H "Authorization: Bearer ..." 'localhost:8000/places?q=top&lat=42.34&lng=-71.10&radius_m=10000'`
   - Save / list saved / unsave / list saved → verify state transitions
3. **Nothing committed yet.** Branch is one commit ahead of `main` (`e15307a TYP-18 ruff format`); all the actual route/repo/schema work is uncommitted.

**Recommended path:** seed manually → curl-test all 4 → commit → open PR to `dev`. Keeps Google Places integration as a clean follow-up ticket.

---

## Concepts Alan now has solid grasp on (added this session)
- Layered architecture in practice (route vs repo vs schema responsibilities)
- Why `services/` is intentionally empty (and when it earns its keep)
- Two-stage spatial filter (bounding box prefilter + precise distance)
- pg_trgm GIN indexes accelerating `ILIKE`
- LEFT JOIN to avoid N+1 (computing per-row "is this related" flags)
- `ON CONFLICT DO NOTHING` for idempotent inserts
- When to drop down to raw SQL via `text()` (extension functions)
- Pydantic `response_model` as the API contract
- FastAPI `Query()` for declarative param validation
- `Depends()` for auth + DB session injection

## Concepts NOT yet covered
- Testing strategy (`services/` layer's value flips here)
- Async SQLAlchemy
- Background jobs (ICS generation, ML retrain triggers)
- The actual ML inference path

---

## MVP deadline reminder
**2026-05-08** — backend deployed and curl-testable. ~8 days out. Don't get pulled into Google Places integration on this branch; ship TYP-18 as scoped.
