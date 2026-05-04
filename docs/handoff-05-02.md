# Handoff — 2026-05-02 (TYP-23 feed built; scope reframed to full iOS-with-friends)

## What this handoff is about

This session had two parts: finishing TYP-23 (friend feed) and a long strategic conversation that **rewrote the MVP definition.** The scope changed materially. Future Claude reading this — the prior "backend deployed and curl-testable by 2026-05-08, iOS punted" note in memory is now stale. New direction below.

---

## What was built (TYP-23 friend feed)

`GET /me/feed` — cursor-paginated merged timeline of friends' ratings + saves + completed outings. Same shape pattern as TYP-22 + TYP-21, with one new wrinkle: **three heterogeneous result types in one response.**

### Files added
```
backend/app/schemas/feed.py                  FeedRatingOut / FeedSaveOut / FeedOutingOut / FeedResponse
backend/app/repositories/feed.py             feed_saves / feed_outings / feed_ratings (raw text() for ratings)
backend/app/services/feed.py                 get_feed (friend lookup → 3 queries → tag-and-merge → cursor)
backend/app/routes/feed.py                   GET /me/feed
backend/app/main.py                          modified — wired feed router
```

### Migration `fe0d54be86d0_feed_indexes.py`
Three indexes powering the feed reads:
- `place_ratings_user_created_idx` — `(user_id, created_at DESC)`
- `saved_places_user_created_idx` — `(user_id, created_at DESC)`
- `outings_creator_completed_idx` — partial `(creator_id, completed_at DESC) WHERE status = 'completed' AND final_rating IS NOT NULL`

Applied cleanly. Verified via `\d` in psql.

### Locked design decisions
1. **Cursor pagination on `created_at`, not offset.** Stable under writes (offsets shift when new rows insert during scroll).
2. **Three heterogeneous shapes with `type` Literal discriminator.** `FeedRatingOut | FeedSaveOut | FeedOutingOut`. iOS decodes by `type`. Beats UNION-NULL-padding in SQL.
3. **Latest-rating-per-place via DISTINCT ON.** Re-rating Joe's Pizza three times shouldn't spam the feed three times. Inner `DISTINCT ON (user_id, place_id) ORDER BY user_id, place_id, created_at DESC` then outer `ORDER BY created_at DESC LIMIT`.
4. **Raw `text()` for ratings query.** DISTINCT ON + 2 JOINs + outer re-sort is awkward in SQLAlchemy ORM. Same precedent as `places` search.
5. **3 separate queries merged in Python, not SQL UNION.** Each repo over-fetches `limit` rows, service does `list.sort` and trims. At most 3×limit items — microseconds.
6. **`.label()` to align ORM columns with schema fields.** `Outing.completed_at` → `created_at` (so all 3 streams sort uniformly), `User.user_id` → `actor_id`, `Place.name` → `place_name`.
7. **Self-exclusion deferred.** Currently feed is "friends only" by design — your own activity will get a separate `/me/activity` endpoint (mirror).
8. **Empty-friends short-circuit.** No friends → return empty without hitting the DB three times.
9. **Filter to truly-completed outings.** `status='completed' AND final_rating IS NOT NULL`. In-progress / cancelled / unrated outings stay out of the feed.
10. **`next_cursor` is null at end-of-feed.** If `len(items) < limit`, the page wasn't full → return null so iOS knows to stop fetching.

### Status
Code complete on branch `typ-23-feed`. Not yet committed/pushed/PR'd. **Not yet manually tested** (same pattern as TYP-21, TYP-22 — code-complete-then-test).

---

## The big reframe — scope changed

### What was true coming in
Per memory and prior handoff: MVP = backend deployed + curl-testable by 2026-05-08. iOS explicitly punted to a future phase.

### What changed today
Alan re-evaluated. Two trigger conversations:

1. **Friend feedback on rating noise.** Friend pointed out place ratings are confounded by event quality (rating MSG based on which artist played). Real ML problem; for MVP it self-corrects via N + per-user personalization. Doesn't change scope, but raised the question of whether the consolidator-only MVP is "shiny enough."

2. **"Doesn't shine without prediction."** Alan worried recs need to be in MVP. I pushed back: cold-start makes recs impossible without rating data — *which the consolidator gathers*. Sequence is consolidator → users → ratings accumulate → recs unlock. Beli/Letterboxd shipped this exact way.

3. **Demo target = friends.** When asked who the demo is for, Alan said "friends, full experience." That redefines MVP: backend curl-testable is no longer the gate. **Friends actually using the app on iOS** is.

### New scope decision
**v1 (ship target) — everything below is in scope:**
- All backend complete (TYP-9 last endpoint, TYP-20 invitations, TYP-23 feed)
- Backend deployed (Render or Railway, managed Postgres)
- iOS app from scratch (Alan starting cold on SwiftUI)
- Auth, 4-tab skeleton, plan creation, friends + invitations UI, rating flow, profile/activity tab
- Push notifications (so friends don't forget plans)
- Friends feed UI wired to TYP-23 backend
- Multi-stop outing builder
- Recommendations (cold-start tiered: 3 ratings → "places similar to ones you saved", 10 → ML recs)
- TestFlight upload + 5-10 NU friends installed and using

**v1 explicitly out of scope (deferred):**
- MapKit place picker — the search-list picker is good enough for v1; map view is polish
- Apple Developer is **active** (Alan confirmed)

### New deadline posture
**No hard deadline.** Alan: "i dont rlly care how long it takes." The 5/8 date was for the old backend-only definition; that target is now retired. Ship-when-ready, but use realistic checkpoints to keep momentum.

### Realistic timeline math (sanity check)
At 6 hrs/day, 7 days/week (Alan's stated availability):
- Backend close + deploy + activity mirror endpoint: ~30 hrs (~1 week)
- iOS from cold start, all v1 features (auth, scaffold, tab shell, plan flow, invitations UI, friends, rating, activity, feed UI, multi-stop, TestFlight): ~95 hrs of focused work + ~30% learning overhead = ~125 hrs
- Push notifications (backend + iOS): ~14 hrs
- Recommendations (cold-start tiered, tier 0/1 minimum for v1): ~18 hrs (defer tier 2 Ridge until users have 10+ ratings)
- Apple TestFlight review buffer: 2-7 days
- **Total ≈ 187 hrs of focused work = ~31 days at 6 hrs/day = ~4-5 weeks calendar**

**Realistic ship target: mid-to-late June 2026.** Push to early July if recommendations tier 2 (Ridge) gets pulled into v1.

---

## Tickets — current Linear board state (as of 2026-05-03)

Alan created the v1 tickets in Linear. Below = actual ticket numbers, with notes on what's still missing.

### Created and on the board

**Backend:**
- **TYP-9** MVP CRUD endpoints (6/7 — one endpoint left; Alan to confirm what the 7th is)
- **TYP-20** Invitations CRUD endpoints (backend)
- **TYP-24** Backend deployment (Render or Railway)

**iOS infra:**
- **TYP-25** Project scaffold + API client
- **TYP-26** iOS — Auth flow (login + register)
- **TYP-10** SwiftUI skeleton (4 tabs) — *recommend retitling to "iOS — Tab shell" since TYP-25 covers project bootstrap*

**iOS features:**
- **TYP-27** iOS — Invitations UI (incoming) (depends on TYP-20)
- **TYP-28** iOS — Friends tab (list + add friend + requests)
- **TYP-29** iOS — Rating flow
- **TYP-30** iOS — Activity tab (your own log) — *needs new backend `GET /me/activity` mirror endpoint*
- **TYP-31** iOS — TestFlight upload + invite friends

### Still need to be created (Alan to add)

- **iOS — Plan creation flow** — single-event create + place picker + time + invite friends. Biggest single iOS feature (~16 hrs). Required for TYP-27 invitations UI to have anything to accept. **Currently missing from board.**
- **iOS — Friends feed UI** — wires up `GET /me/feed` (TYP-23) to the Feed tab. ~10 hrs.
- **iOS — Multi-stop outing builder** — outing creation, stop reordering, weight slider. ~18 hrs.
- **Push notifications (backend + iOS)** — OneSignal recommended for MVP; ~14 hrs combined.
- **Recommendations (cold-start tiered)** — tier 0/1 (popularity + category match) ships first, tier 2 (Ridge regression) when users hit 10+ ratings. ~30 hrs total; consider splitting.
- **Backend — `GET /me/activity` mirror endpoint** — TYP-23-shaped endpoint filtered to `friend_ids=[me]`. ~4 hrs. Blocks TYP-30.

### Stale tickets to decide on

- **TYP-11** Manual "log a past plan" flow — predates the reframe. Achievable via existing endpoints today (POST event with past `scheduled_for`, POST `/outings/{id}/rate`). **Recommendation: defer to v2.** Friends starting on the app will plan forward; retroactive logging is a second-week ask.

### Out of scope for v1 (don't create as tickets)

- MapKit place picker — search-list place picker works fine, map view is polish.

---

## SwiftUI learning approach (for cold start)

Alan asked / I recommended:
- **Don't binge tutorials.** One resource (Apple's official Landmarks tutorial — ~4 hours), then build the actual app.
- **Avoid YouTube series.** Too much content, too slow, days lost.
- **Core 80%:** `@State` (view-local), `@Observable` (Swift 5.9+, shared model), `URLSession` + `async/await`, `Codable` for API responses, `NavigationStack`, `TabView`.
- **Google specific things as you hit them.** Most SwiftUI questions have one canonical Stack Overflow / Apple Forums answer.

---

## Open decisions / questions parked

1. **Push notifications: APNs direct vs OneSignal vs Firebase?** Hasn't been picked. OneSignal is fastest to integrate (free tier covers MVP), APNs direct is more "real" but more setup. Decide when starting that ticket.
2. **Hosting choice: Render vs Railway vs Fly.io?** All three handle Python + Postgres. Render is probably simplest for a first deploy. Railway has the best dev UX. Fly.io is best for global-edge but overkill at MVP.
3. **`GET /me/activity` mirror endpoint.** Needs to be built when iOS Activity tab is built. ~4 hours of backend work. Reuses TYP-23 repos with `friend_ids=[me]`.
4. **DELETE /outings/{id} cascade behavior** (open since TYP-19). Will hit FK error if outing has events. Three options: DB CASCADE, null-out, block-delete-unless-empty. Punt until we hit it during testing.
5. **`promote_to_outing` is still stubbed (501).** TYP-19a never built. May or may not matter for v1 — depends on whether the iOS plan UI lets you "convert event to outing" mid-flow.

---

## What state the repo is in right now

Branch: `typ-23-feed`. Untracked files awaiting commit:
- `backend/alembic/versions/fe0d54be86d0_feed_indexes.py`
- `backend/app/schemas/feed.py`
- `backend/app/repositories/feed.py`
- `backend/app/services/feed.py`
- `backend/app/routes/feed.py`
- `backend/app/main.py` (modified — feed router wired)
- `CLAUDE.md` (modified — TYP-23 endpoint + index notes added)
- `docs/RATING_ENDPOINTS.md` (untracked — TYP-21 doc, never committed)
- `docs/FRIENDSHIPS_ENDPOINTS.md` (untracked — TYP-22 doc, never committed)
- `docs/handoff-05-02.md` (this file)

Migration `fe0d54be86d0` has been applied to local Postgres (`alembic current` matches head).

---

## Next session priorities

1. **Smoke-test TYP-23.** Start uvicorn, get a JWT, hit `GET /me/feed` from a user who has friends with ratings/saves/outings. Verify shape, pagination, `next_cursor` behavior, latest-rating dedupe.
2. **Commit + push + PR TYP-23 to main.**
3. **TYP-9 last endpoint** (Alan said it's 6/7 — confirm what the 7th is).
4. **TYP-20 invitations CRUD** (next big ticket; same pattern as TYP-22 friendships).
5. **Decide hosting + start backend deployment ticket.**

After backend is deployed, iOS work begins.

---

## Concepts Alan grasped today
- Cursor pagination (stateless, client-held cursor, `next_cursor: null` as end-of-stream marker)
- Pydantic discriminated unions via `Literal[...]` `type` field
- `from_attributes=True` purpose (read from object dot-attrs vs dict keys)
- DISTINCT ON dedupe pattern (Postgres-specific)
- `.label()` for renaming columns to match schema field names
- Why FastAPI + SQLAlchemy don't compete (different layers — web framework vs DB toolkit)
- Why MVP recs would be worse than no recs (cold-start damages trust)
- Realistic SwiftUI timeline math (cold-start multipliers, learning overhead)

## Concepts NOT yet covered (carried forward)
- Testing infrastructure (pytest fixtures, test DB)
- Async SQLAlchemy
- ML inference (Ridge regression atomic recommender, hierarchical attribution)
- Background jobs (ICS, ML retrain triggers)
- Deployment (Render/Railway + managed Postgres + env var management)
- SwiftUI from zero — the entire iOS arc
- Apple Developer / TestFlight workflow
- Push notifications (APNs / OneSignal)
