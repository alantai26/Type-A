# TYP-60 Handoff — iOS Profile Saved list (populated)

**Status as of 2026-05-15:** Merged in PR #26 (commit `cb37a0a`). Branch was `typ-60-ios-profile-saved-list-populated`.

---

## What shipped in this ticket

### iOS — ProfileView Saved tab populated
Mirrors TYP-58 (Places) and TYP-59 (Outings) tri-state pattern: `nil` → ProgressView, `[]` → existing empty-state card, populated → row list.

- New state: `@State private var savedPlaces: [Place]?` (line 30 in `ProfileView.swift`)
- New loader: `loadSavedPlaces()` — hits `GET /saved_places` (no `lat`/`lng`, so backend sorts alphabetically). No client-side filter or sort.
- New wiring: three loaders fire in parallel in `.task` + `.refreshable` via three `async let`s:
  ```swift
  async let p: () = loadPlaceRatings()
  async let o: () = loadOutings()
  async let s: () = loadSavedPlaces()
  _ = await (p, o, s)
  ```
- New render path: `case .saved:` in `tabContent` switch + `savedPlacesList(_:)` + `savedPlaceRow(_:)`.
- `countFor(tab: .saved)` updated to `savedPlaces?.count ?? 0` (previously hard-coded 0).

**Row visual** (parallel to Places row, two key differences):
- 32pt category-themed icon (reuses `iconName(for: place.category)`)
- Name + category subtext
- **No rank number** (it's not a ranked list)
- **No score pill** (saved ≠ rated)
- **Decorative filled bookmark icon on the right** (`Image(systemName: "bookmark.fill")`, accent color, no tap action in this slice)

### Backend — PlaceOut gains `category`

`schemas/places.py` adds `category: str` to `PlaceOut`. Both `/places` SQLs (`_SEARCH_SQL`, `_NEARBY_SQL`) and both `/saved_places` SQLs (`_LIST_WITH_DISTANCE_SQL`, `_LIST_NO_DISTANCE_SQL`) now SELECT `p.category`. No migration — column already existed on `places`.

This is forward-useful for the Search tab when that's built (TYP-29-ish).

### iOS `Models.swift`

- `Place` gains `category: String`
- `Place.distanceM` is now `Double?` (was the pending iOS-side consumption of TYP-47's nullable `distance_m` on the response — now actually consumed)

### Seed script

`backend/scripts/seed_dev_data.py` adds 2 saved places (`Trillium Brewing`, `Tatte Bakery`), idempotent on `(user_id, place_id)`. Re-runs are no-ops.

---

## Design decisions worth knowing

### Sort order: alphabetical (not save-recency)
The TYP-60 spec originally said "sorted by save recency." We don't have a `saved_places.created_at` column though — Option A schema from TYP-22 is composite PK only.

Decision: sort alphabetically for v1. Save-recency sort is deferred — would need an Alembic migration to add `created_at` to `saved_places`, plus updates to both repo SQLs. Not worth blocking TYP-60 over.

If user complaints surface, file a follow-up ticket.

### Subtext source: backend hydration (not iOS-only)
`Place` didn't previously have `category` on its `PlaceOut` shape. Alternatives considered:

| Option | Decision |
|---|---|
| Just name, no subtext | Rejected — too sparse, didn't match Places-row visual |
| Show coordinates / distance | Rejected — ugly, defeats TYP-47's "no CoreLocation required" goal |
| **Hydrate `category` on the backend** | ✅ Chosen — mirrors TYP-58's `place_name`/`category` pattern, forward-useful for Search |

### Pull-to-refresh refreshes all three tabs
Rather than only refreshing the active tab, the `.refreshable` handler runs all three loaders in parallel. Justification: the user is on Profile — they want a fresh snapshot of their whole profile. Cheap (~3 small queries) and matches mental model.

### Out of scope (deliberately)
- **Tap-to-unsave** from the Profile Saved row. The bookmark icon is decorative. Unsave lives on Search results and Place detail (TYP-18 endpoints exist). Could be added with one `Button` wrapper + `DELETE /saved_places/{id}` call — separate ticket if desired.
- Settings sheet (TYP-61, separate).
- Real friends count (TYP-62, blocked on TYP-43).

---

## Files touched

```
backend/app/schemas/places.py                    +category: str on PlaceOut
backend/app/repositories/places.py               SELECT p.category in both SQLs
backend/app/repositories/saved_places.py         SELECT p.category in both SQLs
backend/scripts/seed_dev_data.py                 SavedPlace inserts (idempotent)
ios/TypeA/TypeA/Models.swift                     +category, distanceM: Double?
ios/TypeA/TypeA/Views/ProfileView.swift          .saved case + savedPlacesList + savedPlaceRow + 3rd loader wiring
CLAUDE.md                                         API endpoints + iOS tickets-complete line
```

No migration. No new SQLAlchemy models.

---

## How to verify locally

1. `cd backend && source venv/bin/activate && python scripts/seed_dev_data.py`  
   Should print `+ save: Trillium Brewing` and `+ save: Tatte Bakery` on first run (or `= save exists` on re-run).
2. Backend running: `python -m uvicorn app.main:app --reload --host 0.0.0.0`
3. iOS: **Cmd+Shift+K → Cmd+R** in Xcode (required — `Place` model gained a field, decoder will throw without a clean build).
4. Profile → Saved tab → 2 rows alphabetical (Tatte first, then Trillium), category icon + bookmark on right.

---

## PR description (copy-paste)

```markdown
## Summary
- iOS Profile Saved tab populated, mirroring TYP-58/59's tri-state pattern (loading / empty / list)
- Backend: `PlaceOut` schema gains `category` (forward-useful for Search tab too) — both `/places` SQLs and both `/saved_places` SQLs now SELECT `p.category`
- iOS `Place` model gains `category: String`; `distanceM` is now `Double?` (consumes TYP-47's optional `distance_m`)
- Seed script adds 2 bookmarked places (`Trillium Brewing`, `Tatte Bakery`) for local testing

## Implementation notes
- Saved row layout: 32pt category-themed icon (reuses `iconName(for:)`) + name + category subtext + decorative filled bookmark icon on the right. No rank, no score pill (not a ranked list, not a rated entity).
- No new state shape — three parallel `async let` calls in `.task` + `.refreshable`, each populating its tab's tri-state.
- No `created_at` on `saved_places` table → sort falls back to alphabetical when called without lat/lng. If save-recency sort becomes desired, separate ticket (needs a migration).

## Test plan
- [ ] `python scripts/seed_dev_data.py` inserts 2 saves (idempotent on re-run)
- [ ] Profile → Saved tab shows 2 rows alphabetical: Tatte Bakery, Trillium Brewing
- [ ] Each row: category icon + name + category text + bookmark on right
- [ ] Pull-to-refresh re-loads all three tabs in parallel
- [ ] Empty state still renders for users with no saves

Fixes TYP-60
```

---

## What's next after this merges

Profile populated-list slice (TYP-58/59/60) is done. Remaining Profile work:
- **TYP-61** (settings sheet, standalone) — logout, edit display name, etc. Currently logout is the temporary button at the bottom of ProfileView.
- **TYP-62** (real friends count, blocked on TYP-43) — currently hardcoded to `0 friends`.

Or pivot to **Plan tab** (large, spec'd in `docs/CURRENT_HANDOFF.md`) or **Search tab** (TYP-29-ish, unblocked by TYP-47).
