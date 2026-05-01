# Handoff — 2026-04-30 ~11:03pm (TYP-19 mostly built, ready for testing)

## Time accounting (best estimate)

I can't measure wall-clock precisely between turns. Based on the scope of work and Alan's stated 6-hr/day pace, today was likely a single long session of ~6 hours of active work split across multiple sittings. The previous handoff doc was at 12:10am on 2026-04-30 (TYP-18 wrap-up); this one is ~23 hours of wall-clock later, ~6 hours of active build time. Use this as a rough log only.

**Checkpoints reached today:**
- TYP-19 design phase locked
- Migration `0fca5c07c957` written, applied (after a stamp/recover dance)
- Schemas: events + outings done
- Repositories: events + outings done (incl. `recalc_scheduled_for`)
- Services: events + outings done (incl. parent-outing edit-gate, lifecycle cascade)
- Routes: events + outings done (16 endpoints, all registering)
- SQLAlchemy `relationship()` bidirectional set up (no migration)

**Not yet done:** manual end-to-end test, push branch, open PR.

---

## What's on the branch

Branch: `typ-19-events-outings-the-plan-tab`. TYP-18 was merged via PR #10 (`1ca581d Merge pull request #10`). Two TYP-19 commits so far:
- `8f877b2 TYP-19 routes, repositories, schema, and services made`
- `e25b2a0 TYP-19 forgot the claud.md`

### Migration `0fca5c07c957_loosen_planning_fields_add_outing_title.py`
- `outings.title` added (`String(255)`, **NOT NULL**, server_default=`""` then dropped — backfill-safe)
- `outings.scheduled_for` → nullable
- `events.scheduled_for` → nullable

Recovery story worth noting in case it happens again: the migration body was pasted *after* a first `alembic upgrade head` ran with an empty body. To recover, we used `alembic stamp 015dcc40c7ef` to rewind the version pointer without running the (real-now) downgrade body, then `alembic upgrade head` ran the real upgrade. **Lesson:** if a migration's pointer and the actual schema are out of sync, `alembic stamp <prev_revision>` is the surgical fix.

### Models updated
- `app/models/outings.py` — added `title: Mapped[str]`, made `scheduled_for: Mapped[datetime | None]`, added `events: Mapped[list["Event"]] = relationship(back_populates="outing", order_by="Event.sequence_position")`, plus `TYPE_CHECKING` import.
- `app/models/events.py` — made `scheduled_for: Mapped[datetime | None]`, added `outing: Mapped["Outing | None"] = relationship(back_populates="events")`, plus `TYPE_CHECKING` import.

### New files
```
backend/app/schemas/events.py            EventCreate / EventUpdate / EventOut
backend/app/schemas/outings.py           OutingCreate / OutingUpdate / OutingOut (embeds list[EventOut])
backend/app/repositories/events.py       create / get / list_by_outing / update / delete / set_status
backend/app/repositories/outings.py      create / get / list_by_creator / update / delete / set_status / recalc_scheduled_for
backend/app/services/events.py           create / update / delete / confirm / unconfirm / cancel  (+ _check_editable helper)
backend/app/services/outings.py          create / update / delete / confirm / unconfirm / cancel
backend/app/routes/events.py             8 endpoints
backend/app/routes/outings.py            8 endpoints
```

### main.py
Both routers wired:
```python
app.include_router(events_routes.router)
app.include_router(outings_routes.router)
```

### CLAUDE.md
Updated `outings(...)` and `events(...)` lines in the data-model block to reflect the loosened nullables and the new `title` column.

---

## API surface added (16 endpoints)

### Events
| Method | Path | Notes |
|---|---|---|
| POST | `/events` | body=EventCreate; creates planning_in_progress; if `outing_id` supplied → validates parent + recalc |
| GET | `/events/{id}` | 404 if not yours |
| PATCH | `/events/{id}` | edit-gate (409 if confirmed, or parent confirmed); recalc parent if scheduled_for changed |
| DELETE | `/events/{id}` | 204; edit-gate; recalc parent unconditionally if had one |
| POST | `/events/{id}/confirm` | **rejects in-outing events** (409 — use parent's confirm); 422 if scheduled_for or place_id null |
| POST | `/events/{id}/unconfirm` | rejects in-outing; 409 if not confirmed |
| POST | `/events/{id}/cancel` | rejects in-outing; 409 if status in {cancelled, completed} |
| POST | `/events/{id}/promote_to_outing` | **stubbed — 501**; service not built |

### Outings
| Method | Path | Notes |
|---|---|---|
| POST | `/outings` | body=OutingCreate; title required |
| GET | `/me/outings` | list_by_creator, ordered scheduled_for DESC NULLS LAST |
| GET | `/outings/{id}` | embeds events |
| PATCH | `/outings/{id}` | edit-gate; only `title` is currently editable |
| DELETE | `/outings/{id}` | 204; edit-gate; **NOTE: will hit FK error if outing has events** (cascade not configured yet — open question) |
| POST | `/outings/{id}/confirm` | requires ≥2 events, all with scheduled_for, all with place_id or custom_location_name; recalc; cascade events → confirmed |
| POST | `/outings/{id}/unconfirm` | cascade events → planning_in_progress |
| POST | `/outings/{id}/cancel` | 409 if cancelled/completed; cascade events → cancelled |

All 16 require Bearer JWT.

---

## Locked design decisions (TYP-19)

### 1. Two-button creation (Path X), not auto-promotion
User explicitly chooses "Create Event" or "Create Outing" up front. Backend: `POST /outings` makes the shell, then `POST /events` with `outing_id=...` adds stops. No implicit promotion via "user added a second event."

### 2. Promote-to-outing endpoint exists (stubbed)
For users who started a standalone event and later want to add stops. Returns 501 for now; service work deferred. The route shape is in Swagger so the API surface is discoverable.

### 3. Loose at create, strict at confirm
Most fields nullable at creation (events: place_id, custom_location_name, scheduled_for, etc.). The validation happens *at confirm time*, not earlier. This lets the iOS UI build up plans piece-by-piece.

**Confirm-time invariants (events):** scheduled_for + place_id non-null.
**Confirm-time invariants (outings):** ≥2 events, every event has scheduled_for, every event has place_id OR custom_location_name (informal stops allowed inside outings — privacy-by-construction).

### 4. Title NOT NULL on outings
Every outing has a title from creation. Migration backfilled empty string; PATCH lets the user change it later.

### 5. `outings.scheduled_for` is materialized + derived
Not user-editable. Stored on the row but always equals `MIN(events.scheduled_for)` for that outing's events. `outings_repo.recalc_scheduled_for(db, outing)` is called by services on event create/update/delete and at confirm time.

### 6. Services layer earned its keep
Unlike TYP-18 (no services), TYP-19's lifecycle/cascade/edit-gate logic justified populating `app/services/`. Repos stay dumb (CRUD only); services raise HTTPExceptions and orchestrate.

### 7. In-outing events: status mirrors parent
Solo events have their own confirm cycle. Events with `outing_id IS NOT NULL` get their status managed by the parent outing's lifecycle endpoints (cascade). The per-event `/confirm`, `/unconfirm`, `/cancel` reject in-outing events with 409 ("operate on the parent outing instead").

### 8. Cancel from planning + confirmed; blocked from terminal
- `cancelled` and `completed` are *terminal* states — no transitions out.
- `cancel` deliberately bypasses the standard `_check_editable` (which would block confirmed) — the confirmed→cancelled transition is the *primary* cancel use case.

### 9. POST for verbs, PATCH for fields (REST design)
`/confirm`, `/unconfirm`, `/cancel`, `/promote_to_outing` are POSTs. They're *named actions* with side effects (cascades, validations, recalc), not field edits. PATCH is reserved for partial updates of editable fields (e.g., `title`, `scheduled_for`, `weight`). Status is *deliberately excluded* from `*Update` schemas — no PATCH-based status sneaking.

### 10. Embedded events in OutingOut via SQLAlchemy `relationship()`
`Outing.events` and `Event.outing` are bidirectional `relationship()` definitions linked by `back_populates`. No migration required — it's pure ORM-side glue. Lets `GET /outings/{id}` return the outing with its events list in one round-trip, no N+1.

### 11. No auto-demote of 1-event outings
A 1-event outing during planning is allowed but can't be confirmed (≥2 rule). The user explicitly decides what to do: add another event, or DELETE the outing. **Open issue logged:** `DELETE /outings/{id}` will hit FK integrity error if events exist — no cascade configured. Defer until we hit it during testing.

### 12. PATCH /outings only edits `title`
Everything else is derived (scheduled_for) or status-only (via lifecycle endpoints).

---

## Major questions Alan raised (and how they got answered)

1. **"Why POST for /cancel and not PATCH?"** → Industry convention: PATCH for editable fields, POST for named actions with side effects. Status is excluded from `*Update` schemas to enforce this boundary.
2. **"Should we have a services layer?"** → Yes, *now*. The convention from CLAUDE.md was "services only when there's orchestration" — TYP-19 has cross-repo orchestration (cascades, recalc, edit-gates), so the layer earns its keep.
3. **"Can a standalone event be promoted to an outing?"** → Yes, via `POST /events/{id}/promote_to_outing`. Stubbed for now; deferred.
4. **"Do we need a migration for `relationship()`?"** → No. Pure-Python ORM glue, no DB schema change.
5. **"What is `model_config = ConfigDict(from_attributes=True)`?"** → Pydantic v2's "read from object attributes, not just dict keys." Needed on `*Out` schemas because they're often fed SQLAlchemy ORM objects.
6. **"What is `events_repo`?"** → An import alias (`from app.repositories import events as events_repo`) — disambiguates the three `events` modules (`models.events`, `repositories.events`, `routes.events`).
7. **"What does `back_populates` mean?"** → Tells SQLAlchemy two `relationship()` definitions are two sides of the same connection. Keeps both sides in sync in memory.
8. **"What does `.all()` do?"** → Triggers query execution and returns the rows as a list. Without it, you have a `Query` object, not results.
9. **"Why doesn't services have `get`?"** → Pure reads have no logic to orchestrate. Routes call repos directly for reads.
10. **"How do friends test the iOS app?"** → TestFlight (Apple Developer $99/yr). Apply *immediately* — verification can take 24-72h. Friends install TestFlight, click your public link, tap install.
11. **"`completed_at` at create-time for past events?"** → No. Cleaner mental model: every event starts `planning_in_progress`. A "past event" is one with past `scheduled_for` walked through the lifecycle. Same path for past or future events.
12. **"If I delete an event leaving 1 in an outing, does it auto-collapse?"** → No. 1-event outings are allowed during planning. User explicitly decides next move.
13. **"Cancel from confirmed?"** → Yes — cancel is the primary verb for "plans changed." Block only terminal states (`cancelled`, `completed`).
14. **"Can events outside outings still be informal (Jim's house)?"** → Schema allows it (events.place_id nullable + custom_location_name). But solo informal events can't be **rated** because place_ratings.place_id has FK to places. Rating is auto-impossible — privacy by construction.

---

## What's NOT done — open before TYP-19 closes

1. **No manual end-to-end test.** All routes register, but no endpoint has been hit with a real request yet.
2. **No JWT obtained for testing.** Need to either provision a test user in Supabase dashboard or use an existing one to grab a token.
3. **No seed data in `places`.** Solo event confirm requires `place_id IS NOT NULL` → can't test that path without at least one place row. (Outing confirm with `custom_location_name` works without seed data.)
4. **`promote_to_outing` service is unimplemented** — stub returns 501. Defer to TYP-19a.
5. **`DELETE /outings/{id}` cascade behavior is undefined.** If outing has events, it'll hit a FK integrity error. Three options for later: (a) DB-level CASCADE, (b) null-out events on outing delete, (c) block delete unless empty. Punt until we hit it.
6. **Nothing pushed yet.** Branch is local-only. PR not opened.

---

## Next steps (tomorrow)

**Recommended order:**

1. **Get a JWT.** Sign in via Supabase (test user) → grab `access_token`.
2. **Manual smoke test.** Start uvicorn, then run through:
   - `curl /health` (no auth)
   - `POST /me` → confirm auth pipeline still works
   - `POST /outings` with title
   - `GET /me/outings` → list shows the new one
   - `POST /events` with `outing_id=<that outing>` and `custom_location_name="Jim's house"` and `scheduled_for=...` → twice
   - `POST /outings/{id}/confirm` → cascade should set both events to confirmed
   - `POST /outings/{id}/unconfirm` → cascade back
   - `PATCH /events/{id}` to change scheduled_for → outing's scheduled_for should auto-recalc on next read
3. **Push + open PR to main (or dev if that branch exists yet).**
4. **(Stretch)** Implement `promote_to_outing` if there's time.

---

## Status of the bigger arc

- **TYP-19 code-complete.** Ready for testing.
- **MVP deadline 2026-05-08.** ~8 days out.
- **Apply for Apple Developer Program ASAP.** Verification can take 24-72 hours; this is the time-critical blocker for any iOS distribution path.
- **Cuts already locked for MVP:** Google Places (manual seed instead), real ML inference (stubs only), invitations + friendships (cut), notifications + ICS (cut).
- **Decision pending:** iOS via TestFlight vs web prototype. Alan leaning iOS.

---

## Concepts Alan now has solid grasp on (added today)

- The full Route → Service → Repository → DB stack
- When services are needed (cross-repo orchestration) vs when they're noise (pure reads)
- `Mapped[]` + `relationship()` + `back_populates` for SQLAlchemy bidirectional links
- Pydantic schemas: `*Create` (request body), `*Update` (PATCH partial), `*Out` (response, with `from_attributes=True`)
- `model_dump(exclude_unset=True)` for PATCH semantics
- `**kwargs` pattern for flexible repo update functions
- HTTP status codes: 404 (hide existence) vs 403 vs 409 (state conflict) vs 422 (validation)
- POST-for-verbs vs PATCH-for-fields REST convention
- `import X as Y` pattern for disambiguating same-named modules across layers
- Alembic recovery via `stamp` when pointer/schema desync
- Lazy SQL: `db.query(...)` returns a `Query`; `.all()` / `.first()` / `.scalar()` execute it
- Why GET endpoints don't always need a service layer

## Concepts NOT yet covered
- Testing infrastructure (pytest fixtures, test DB)
- Async SQLAlchemy
- ML inference (Ridge regression for atomic recommender)
- Attribution model decomposition
- Background jobs (ICS generation, ML retrain triggers)
- Deployment (Fly.io / Railway / managed Postgres)
- iOS / SwiftUI client (TestFlight distribution)

---

## File diff vs main (rough)

| File | Status |
|---|---|
| `backend/alembic/versions/0fca5c07c957_loosen_planning_fields_add_outing_title.py` | new |
| `backend/app/models/outings.py` | modified (title, nullable scheduled_for, relationship) |
| `backend/app/models/events.py` | modified (nullable scheduled_for, relationship) |
| `backend/app/schemas/events.py` | new |
| `backend/app/schemas/outings.py` | new |
| `backend/app/repositories/events.py` | new |
| `backend/app/repositories/outings.py` | new |
| `backend/app/services/events.py` | new |
| `backend/app/services/outings.py` | new |
| `backend/app/routes/events.py` | new |
| `backend/app/routes/outings.py` | new |
| `backend/app/main.py` | modified (router wiring) |
| `CLAUDE.md` | modified (data-model line for outings/events) |
