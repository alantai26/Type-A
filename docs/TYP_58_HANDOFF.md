# TYP-58 Handoff — iOS Profile Places List (populated)

Per-ticket handoff for Linear TYP-58. Spec lives in `docs/05-09_HANDOFF.md §5` and the Linear ticket. Session started 2026-05-11, finished 2026-05-12.

## ▶ Read this first (state as of 2026-05-12 end of session)

TYP-58 is **functionally complete and working in the local simulator**, but **not committed and not pushed**. The next session's first job is to ship this PR.

Working tree state (run `git status` to confirm):
- **Branch**: `typ-58-ios-profile-places-list-populated`
- **Unstaged TYP-58 work** (ready to commit):
  - `backend/app/schemas/place_ratings.py` — added `place_name`, `category` fields
  - `backend/app/repositories/place_ratings.py` — joined `Place` in `list_by_user`
  - `backend/app/routes/place_ratings.py` — dropped `-> list[PlaceRating]` annotation
  - `backend/scripts/seed_dev_data.py` — new dev seed helper
  - `ios/TypeA/TypeA/Models.swift` — added `PlaceRating` struct
  - `ios/TypeA/TypeA/Views/ProfileView.swift` — populated list rendering, tier pills, dividers, pull-to-refresh
  - `docs/TYP_58_HANDOFF.md` — this file
- **Unstaged TYP-38 follow-up docs** (left over from previous session, fold into this commit or a separate one):
  - `CLAUDE.md` — iOS notes update
  - `docs/CURRENT_HANDOFF.md` — TYP-38 merge entry
- `ios/TypeA/Local.xcconfig` is currently pointed at Alan's LAN IP (`http://192.168.x.x:8000`) for local-simulator dev. **Already gitignored** so it can't accidentally land in the PR — leave it as-is for the next session's local dev work.

Next steps (in order):
1. Verify nothing breaks via Cmd+B + simulator smoke test
2. Stage the files listed above (specifically — **not** `Local.xcconfig`)
3. Commit with message `TYP-58 Profile Places list (populated)` (no "Fixes" — TYP-58 still has follow-up edge cases, but ticket can be marked Done after merge)
4. Push, open PR targeting `dev`. PR description: list backend hydration + iOS populated rendering + tier pills + dev seed script + pull-to-refresh
5. Merge to `dev`. Then mark TYP-58 Done in Linear.

The full breakdown of what got built is below.

---

## Status

| Slice | State |
|---|---|
| Backend: hydrate `GET /me/place_ratings` with place_name + category | ✅ done |
| iOS: `PlaceRating` model | ✅ done |
| iOS: fetch on `.task` | ✅ done |
| iOS: tri-state (`nil` / `[]` / populated) rendering | ✅ done |
| iOS: ranked rows (rank # + icon placeholder + name + category + score) | ✅ done |
| iOS: tab-strip counts hydrated from real data | ✅ done |
| iOS: tier-colored score pills (green/amber/red) | ✅ done |
| iOS: dividers between rows | ✅ done |
| iOS: pull-to-refresh | ✅ done |
| Dev seed script (`backend/scripts/seed_dev_data.py`) | ✅ done |
| Real photos | ❌ v1.1 (TYP-53 Google Places) |
| Tapping a row → place detail | ❌ TYP-49 |

## File map

### Backend

`backend/app/schemas/place_ratings.py` — added `place_name: str` and `category: str` to `PlaceRatingOut`. Pydantic's `from_attributes=True` reads these from the row attributes the repository now returns.

`backend/app/repositories/place_ratings.py` — `list_by_user` no longer returns `list[PlaceRating]` ORM instances. Instead the inner DISTINCT ON subquery (unchanged) is joined to `Place` in the outer `db.query(...)` with `.label("place_name")` so the row attribute name matches the schema field. Pattern lifted verbatim from `backend/app/repositories/feed.py:12` (`feed_saves`).

`backend/app/routes/place_ratings.py` — removed the now-incorrect `-> list[PlaceRating]` annotation on `list_my_place_ratings`. FastAPI's `response_model=list[PlaceRatingOut]` handles serialization; the function annotation was the only place that lied about the new return shape.

No migration needed — we changed read-time joining, not the schema.

### iOS

`ios/TypeA/TypeA/Models.swift` — added `PlaceRating` struct matching the backend response (camelCase via `convertFromSnakeCase` decoder).

`ios/TypeA/TypeA/Views/ProfileView.swift` — central changes:
- `@State private var placeRatings: [PlaceRating]?` (tri-state: `nil` = loading, `[]` = empty, populated = render list)
- `.task { await loadPlaceRatings() }` + `.refreshable { await loadPlaceRatings() }` on the ScrollView
- Body's `emptyStateCard` replaced with `tabContent` — a `@ViewBuilder` switch:
  - Places tab + `nil` → `ProgressView`
  - Places tab + `[]` → existing `emptyStateCard`
  - Places tab + populated → `placesList(ratings)`
  - Outings / Saved → `emptyStateCard` (their fetches are TYP-59 + TYP-60)
- `tabStripItem` now calls `countFor(tab:)` instead of hardcoded `"0"` — Places shows the real count, Outings/Saved still 0 until their tickets ship
- `placeRatingRow(rank:rating:)` — HStack: rank → icon-on-orange-tint photo placeholder (32pt rounded square) → name+category VStack → Spacer → `scorePill`. `.padding(.vertical, 14)` for breathing room
- `scorePill(_:)` + `scoreColors(for:)` — tier-coloured capsule pill, thresholds at 6.7 and 3.4, palette from `docs/05-09_HANDOFF.md §4` (fun green #1F8A3F / okay amber #8B6914 / didn't like red #C62828) on light tinted backgrounds
- `iconName(for:)` — SF Symbol map for category strings (activity / restaurant / bar / brewery / cafe / park / fallback `mappin`)
- `loadPlaceRatings()` — `try await APIClient.shared.request("/me/place_ratings")`, errors fall back to `[]` with a print

### Dev helper

`backend/scripts/seed_dev_data.py` — idempotent local seed for dev. Inserts the Figma's 5 Boston places + ratings. Self-bootstraps `sys.path` and `dotenv` so `python scripts/seed_dev_data.py` runs from `backend/` without `-m`. Also patches the user's `display_name` if the auto-provisioner gave them the email-prefix fallback (`talan4030` → `Alan Tai`).

Safety rail: prints the DB host first and refuses to write if the URL points anywhere other than `localhost` / `127.0.0.1` without explicit `yes` confirmation.

## Empty-state copy + thresholds (locked)

- **Tier thresholds**: ≥ 6.7 green, 3.4 ≤ x < 6.7 amber, < 3.4 red. Cleaner thirds of 0–10 than the §4 spec (which used 7.0 / 4.0 boundaries); Alan picked 6.7 / 3.4 in this session.

## Local dev loop

iOS Simulator on some Xcode versions can't reach the Mac's loopback (`localhost` / `127.0.0.1` from inside the simulator gets ECONNREFUSED). Workaround used in this session:

1. Find the Mac's LAN IP: `ipconfig getifaddr en0`
2. Run uvicorn bound to all interfaces: `python -m uvicorn app.main:app --reload --host 0.0.0.0`
3. Set `APIBaseURL` in `Local.xcconfig` to `http://<LAN_IP>:8000`
4. Rebuild the iOS app

`Local.xcconfig` is already gitignored so the LAN IP can't leak into a commit. Each dev fills in their own copy from the inline comments.

Seed the local DB: `python scripts/seed_dev_data.py` (requires `cd backend && source venv/bin/activate`).

## Known stubs (intentional)

| Stub | Why | Fix path |
|---|---|---|
| Icon-on-tint photo placeholders | Real photos are v1.1 | TYP-53 (Google Places) swaps `RoundedRectangle.fill` for `AsyncImage` — layout already supports the drop-in |
| Row tap is no-op | Place detail screen doesn't exist | TYP-49 |
| `iconName(for:)` only knows 7 categories | We don't have a curated category list yet | Extend the switch as real categories appear in seeded/Google data |

## Known SourceKit noise

Same red squiggles as TYP-38:
- `Cannot find 'AuthStore' / 'TabSelectionStore' / 'AppTab' / 'PlaceRating' in scope`
- `Color(uiColor: .secondarySystemBackground)` — "No exact matches"

Code compiles + runs. Clears on Cmd+Shift+K → Cmd+B. See `docs/TAB_SWITCHING_UNDERSTANDING.md` "Common gotchas" for the broader pattern.

## Next slice — recommended sequence

The three sibling tickets created when TYP-38 was split are all ready to start:

1. **TYP-59 — Profile Outings list (populated).** Most natural next move. Same shape as TYP-58 but data source is `GET /me/outings` filtered client-side to `status == "completed" && final_rating != nil`. Reuse the row pattern + score pill + divider treatment.
2. **TYP-61 — Profile settings sheet.** Independent of TYP-59/60 and deletes the temporary Logout once it lands. Includes `display_name` editing UI (so the seed-script workaround becomes unnecessary).
3. **TYP-60 — Profile Saved list (populated).** Blocked on TYP-47 (make `q`/coords optional on `/saved_places`). Don't start until TYP-47 ships.
4. **TYP-62 — Profile real friends count + mini-avatars.** Blocked on TYP-43.

Header scroll-vs-pin can stay deferred until all three lists exist and the screen has real scroll length.

## Out of scope for TYP-58 (do NOT pull in)

- Place detail screen (TYP-49)
- Real photos (v1.1 TYP-53)
- Outings list (TYP-59)
- Saved list (TYP-60)
- Settings sheet (TYP-61)
- Friend-view profile (TYP-50)
