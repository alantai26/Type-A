# TypeA — Current Handoff

Living doc. Updated as decisions are made, scope shifts, or tickets merge. For deeper per-ticket archaeology see `TYP_XX_HANDOFF.md` files; for evergreen architectural reference see the per-topic docs in this folder.

---

## Recent decisions

### 2026-08-19 (later) — TYP-69 shipped: synthetic ML training data + security hardening

- **Merged in PRs #34 + #35** (commits `6d673aa`, `703eb5c`). Branch `typ-69-mvml-2-hand-curated-seed-data-alan`. Full breakdown in `docs/TYP_69_HANDOFF.md`.
- **`backend/scripts/seed_ml_data.py`** — a generator, not a fixture list. 8 personas × 5 categories in a `PREFERENCE_MATRIX` of `(low, high)` rating ranges; 26 real Boston places; ratings sampled uniformly within each cell at `--coverage 0.85`; `--seed 42` default for reproducibility. Built on TYP-68's helpers.
- **The matrix IS the eval target.** TYP-70's eval script must recover each cell's midpoint from the fitted user×category interaction. `omnivore` (flat 6–8) and `hater` (flat 2–4) are deliberate degenerate personas — they prove the model learns a *user intercept* separately from *category preference*.
- **Outings built for TYP-71**: each pairs a top-2-preference stop at `weight=0.7` with a bottom-2 stop at `weight=0.3`; `final_rating` is the exact weighted sum. The attribution model has literal ground truth to be scored against.
- **MAE floor ≈ 0.5** — uniform sampling within a 2-wide range bounds the best achievable error. A model at ~0.5 has hit the ceiling, not a bug.
- **Local DB state**: 10 users (8 synthetic), 32 places (26 new), 193 ratings (168 synthetic), 47 outings (40 synthetic), 94 events. Verified 2026-08-21.
- **⚠️ `places.category` is not a closed taxonomy** — pre-existing seed rows carry `Brewery`, `park`, and lowercase `restaurant` alongside the 5 canonical values. `restaurant` vs `Restaurant` would become two one-hot columns for one concept. TYP-70 must handle this explicitly (normalize, filter, or clean). No CHECK constraint exists on the column, unlike `status`/`rsvp_status`; adding one needs a migration + backfill — worth filing, out of mvML scope.
- **Re-running the script appends ratings** (TYP-21 append-only). TYP-70 must train on latest-per-`(user, place)` via `DISTINCT ON`, or a re-run silently double-weights every observation.
- **`.claude/hooks/protect-files.sh` hardened** — was path-only, now also scans outgoing Write `content` / Edit `new_string` for secret-shaped values (env assignments with real values, DB URLs with embedded credentials, inline private keys, `AKIA` IDs, long `SECRET|TOKEN|PASSWORD` values). Triggered by a real leak this session: the local `DATABASE_URL` was copied *out of* `CLAUDE.md` into a session-notes doc, which the path-based check allowed. Literal URLs/IPs redacted from `CLAUDE.md`, `ALEMBIC_NOTES.md`, `CURRENT_HANDOFF.md`, `TYP_61_HANDOFF.md`. An `.env.example` early-exit was needed so the template stays editable.
- **`docs/SECURITY_CONSIDERATIONS.md` added** — living audit (✅ Have / ⚠️ Partial / ❌ Missing / N/A) with 7 prioritized pre-TestFlight tickets. Biggest real gaps: git-history secret scan, security headers middleware, Dependabot, rate limiting on `POST /place_ratings` + `/friends/requests`, cross-user authz sweep. **None block mvML.**

### 2026-08-19 — mvML path locked; TYP-68 (seed scaffolding) shipped

- **mvML sequence chosen** to unblock ML work without waiting on iOS UI or real users. Skips TestFlight + Rate/Search/Plan UI in favor of hand-curated synthetic seed data. Real user-driven data collection resumes post-mvML.
- **Filed 5 tickets**: TYP-68 (seed scaffolding, 2pt), TYP-69 (hand-curated data by Alan, 4pt), TYP-70 (Atomic Recommender ridge + eval, 8pt), TYP-71 (Attribution Model hierarchical, 8pt), TYP-72 (iOS Recommended Score display, 2pt). Sequence encoded via Blocks/Blocked-by in each Linear description.
- **TYP-68 shipped**: `backend/scripts/seed_dev_data.py` refactored to expose 5 idempotent helpers taking an explicit `db: Session` — `create_user`, `create_place`, `create_rating` (append-only per TYP-21), `create_saved`, `create_outing_with_stops`. Outing helper auto-inserts the creator `OutingInvitation` with `rsvp_status='accepted'` to mirror TYP-19's API retrofit so seeded state matches API-created state.
- **`main()` refactored** to use the helpers — original TYP-58/59/60 seed rows still land unchanged. Real user is still fetched (not `create_user`d) to avoid duplicating the Supabase-issued `user_id`.
- **CLAUDE.md was stale on one detail**: `saved_places.created_at` DOES exist as a column (TYP-60 handoff claimed it was deferred). `create_saved` accepts an optional `created_at` accordingly. Worth updating in a doc-cleanup pass.
- **Rating UX for real users (post-mvML)**: Beli-style — 3-tier picker → binary comparison against previously-rated items in the same tier → derived numeric rating. First-in-tier accepts the tier midpoint (~8.5 / 5.5 / 2.5). Matches TYP-45's design.

### 2026-08-17 — TYP-67 shipped: PlaceDetailView UI/UX polish

- Design-system pass on the functional shell that shipped with TYP-49. Function-first was in PR #29; polish is this PR.
- **Header**: 60pt orange-tinted category icon block, 32pt SF Pro Rounded bold place name, category subtext, lat/lng gated (hidden when both are `0` — matches the sentinel-construction path from Places-tab entries).
- **Section headers unified** at `18pt semibold` across "Your rating" and "Friends activity."
- **Action pills** — Save flips between filled-accent (Save) and outlined-accent (Saved); Rate + Plan stay `outlinedDisabled` with grey separator border until TYP-29 + Plan tab land.
- **`scorePill(_ rating:)` locked to your Profile tier thresholds** (green ≥6.7, amber ≥3.4, red below) and reused in both your-rating and friends-activity rows. Second consumer of the pattern; TYP-64 (extract to reusable component) still waits for consumer #3.
- **Friends-activity rows redesigned**: 40pt initials avatar (accent-tinted, `initialsAvatar` duplicated locally from `ProfileView` — same rule-of-three logic) + name (15pt semibold) + `"Rated · 3d ago"` / `"Saved · 3d ago"` subtitle + trailing element (score pill for ratings, filled bookmark icon for saves). Uses `AnyView` to unify the two branches into one row builder; acceptable at friends-list sizes.
- **Local `relativeTime(_:)` helper** wraps `RelativeDateTimeFormatter` with `.short` style. Reused in the your-rating row (replaces the redundant "You rated this X.X" text next to the pill) and in every friends-activity row.
- **Empty states warmed** — "No friends have rated or saved this yet" in italic secondary. Matches the tone of the Profile-tab empty states.
- **Save-button state hydration gap surfaced (out of scope)**: entries from the Places tab construct `Place` from `PlaceRating` rows which don't carry `is_saved`, so the button initially shows the not-saved state even for bookmarked places. Fix would be a proper `GET /places/{place_id}` endpoint that returns the full `PlaceOut` for the caller. Not filed yet.
- **Dev-env recovery this session** (unblocker, not scope of TYP-67): dead Supabase project killed both auth AND `DATABASE_URL` (which had drifted to point at Supabase's Postgres instead of local). New Supabase project created, `.env` `DATABASE_URL` moved to local Postgres.app (see `.env` for the exact URL), `Local.xcconfig` LAN IP refreshed to the current Mac's LAN address, seed data reassigned from the dead old-Supabase user_id to the new one via a one-shot `UPDATE ... SET user_id/creator_id = ...` transaction.

### 2026-05-22 — TYP-49 + TYP-65 merged (+ TYP-21 drive-by); TYP-66 and TYP-67 filed

- **PR #28 (TYP-65)** merged at `5d2d39a` — backend `/places/{id}/friends_activity` endpoint. **PR #29 (TYP-49)** merged at `de0088d` — iOS PlaceDetailView functional v1 + TYP-21 drive-by fix to `/places/{id}/my_rating` (latent ORM/Pydantic schema mismatch that 500'd before TYP-49 became the first consumer).
- **TYP-49 shipped functionally, not visually.** Per Alan's new "function first, polish last" preference (memory: `feedback_function_first_ui.md`), the screen renders unstyled `Text` rows and default Buttons in this PR. Visual layer is now TYP-67 — sequel ticket filed for design-system pass.
- **`requestVoid` added to APIClient** — first iOS consumer of a 204 endpoint (Save/Unsave). Other 204 endpoints (friend requests accept/reject, unfriend, etc.) can use the same helper when they wire up.
- **Discriminated-union pattern reused.** `FriendsActivityItem` mirrors `FeedItem`'s custom-`Decodable`-with-`type`-discriminator pattern in `Models.swift`. Pattern is now established for any future polymorphic API response.
- **`Place` lat/lng = 0 sentinel** — when entering PlaceDetailView from a `PlaceRating` (Places tab), we construct a `Place` with `latitude=0, longitude=0` because PlaceRating doesn't carry coordinates. PlaceDetailView's header hides the lat/lng line when both are zero. Future cleanup: add `GET /places/{place_id}` for proper hydration; not filed yet.
- **`docs/TYP_61_HANDOFF.md` finally landed.** Was uncommitted since PR #27 closed; rode along in PR #29 with the rest of the doc updates.
- **TYP-66 filed** (separate ticket) — attendee tracking on outings + events. Came out of an unrelated product question during TYP-49 ("can friend activity also say who they went with"). Decision: out of scope for TYP-49; separate concept (attendance ≠ invitation), needs schema migration + iOS sheet at outing-completion. Estimate snapped to 8pt by Linear (cap).
- **TYP-67 filed** — UI/UX polish on PlaceDetailView. Next up.

### 2026-05-15 (later) — TYP-61 + TYP-41 merged: Profile settings screen + bio field

- **Merged in PR #27** (commit `33fb8de`). Branch was `typ-61-ios-profile-settings-sheet`. Two Linear tickets in one PR: TYP-41 (backend bio field) + TYP-61 (iOS settings screen). Bundled because the iOS work is meaningless without the column.
- **Backend (TYP-41)**: Migration `b416388ba296` adds `bio TEXT NULL` to `users`. `UserOut` exposes it; `UserUpdate` enforces 160-char cap server-side via `Field(default=None, max_length=160)`. Repo + route updated. `Text` column (unbounded) — the 160-char cap is a presentation/API concern, not a storage one.
- **iOS (TYP-61) — new `SettingsView.swift`** pushed from `ProfileView`'s gear via a `NavigationLink`. `MainTabView:18` now wraps `ProfileView()` in `NavigationStack { ... }` — only the Profile tab gets one; other tabs unchanged.
- **Deliberate divergence from the ticket**: settings is a **navigation push, not a modal sheet**. Settings is hierarchical (Instagram/X/Threads convention), and push keeps the tab bar visible. Ticket text said "modally"; that's an implementation hint, not a UX contract.
- **Edit pattern is row-style, not inline TextFields**: bold label + grayed value + pencil icon. Tap → `EditFieldSheet` (sheet from within the pushed view) with a focused `TextField` and a Cancel/Done toolbar. Bio variant has 160-char clamp + `count / 160` counter. Done writes draft back to parent state; the top-level Save button in `SettingsView`'s toolbar fires the single `PATCH /me` for all changes.
- **Save UX gates**: Save button disabled until something actually differs from `authStore.currentUser`. Empty display name → inline validation error, no PATCH. After success, `authStore.currentUser = updated` directly — Profile's identity block re-renders without a re-fetch.
- **Bio clearing semantics**: repo's `if bio is not None: user.bio = bio` means clients can't send NULL to clear bio. iOS always sends `bio: trimmed` (even empty string), so wipe-the-bio in UI = empty string in storage. UI treats null and empty identically.
- **Logout moved into `SettingsView`** as a destructive-role button. The temporary red Logout button at the bottom of `ProfileView` is gone, along with the orphan `isSigningOut` state + `signOut()` method (well, two leftovers still untouched — cosmetic only, see TYP_61_HANDOFF).
- **Section placeholders for Notifications / Privacy / Blocked users** ship as `.disabled(true)` "Coming soon" rows — ticket asked for the dividers so v1.x can fill them in without re-arranging.
- **Drive-by APIClient date fix**: latent bug surfaced this session. Postgres emits microsecond-precision timestamps (`.523774`); Swift's strict `.iso8601` strategy rejects fractional seconds entirely. Replaced with a `.custom` strategy that normalizes to milliseconds then parses with `.withFractionalSeconds`, falling back to plain ISO8601. Applies to every decoded response, not just `/me`.
- **Identity block updated**: `currentUser?.bio` rendered when non-nil; italic "Tap settings to add bio" placeholder when nil.
- See `docs/TYP_61_HANDOFF.md` for the full per-ticket breakdown.

### 2026-05-15 — TYP-60 merged: Profile Saved list populated

- **Merged in PR #26** (commit `cb37a0a`). Branch `typ-60-ios-profile-saved-list-populated`.
- **iOS**: `ProfileView`'s Saved tab populated with the same tri-state pattern as Places + Outings. Row layout: 32pt category-themed icon + name + category subtext + decorative filled bookmark icon rightmost. **No rank** (it's not a ranked list), **no score pill** (saved ≠ rated).
- **Three loaders fire in parallel** in `.task` + `.refreshable` via three `async let`s: `loadPlaceRatings()`, `loadOutings()`, `loadSavedPlaces()`. Pattern: `_ = await (p, o, s)`.
- **Backend hydration**: `PlaceOut` schema gains `category: str` to power the Saved row's subtext. Both `/places` SQLs (`_SEARCH_SQL`, `_NEARBY_SQL`) and both `/saved_places` SQLs (`_LIST_WITH_DISTANCE_SQL`, `_LIST_NO_DISTANCE_SQL`) now SELECT `p.category`. Forward-useful for Search results too. No migration.
- **iOS `Models.swift`**: `Place` gains `category: String`; `distanceM` is now `Double?` (consumes TYP-47's nullable `distance_m`).
- **Seed script** (`backend/scripts/seed_dev_data.py`): adds 2 bookmarked places (`Trillium Brewing`, `Tatte Bakery`), idempotent on `(user_id, place_id)`.
- **Sort order**: alphabetical when no caller location. `saved_places` has no `created_at` column → save-recency sort would need a migration; deferred. Reasonable for v1.
- **Out of scope**: tap-to-unsave from Profile (separate ticket if needed — currently lives on Search and Place detail), settings sheet (TYP-61), real friends count (TYP-62 blocked on TYP-43).
- See `docs/TYP_60_HANDOFF.md` for the full per-ticket breakdown.

### 2026-05-14 — TYP-47 merged: optional `q` on /places, optional `lat`/`lng` on /saved_places

- **Merged in PR #25** (commit `0f9c205`). Branch `typ-47-verify-get-places-saved_places-work-for-nearby-only-mode`.
- `GET /places`: `q` is now optional. When omitted, returns all places in `radius_m` ordered by distance ASC. `lat`/`lng` stay required (it's a location search by definition).
- `GET /saved_places`: `lat`/`lng` are now optional. When omitted, `distance_m` is null and rows are sorted alphabetically. Profile-tab use case: load bookmark list without prompting CoreLocation permission.
- `PlaceOut.distance_m` is now `Optional[float]`. Backend ready; iOS-side `Place.distanceM = Double?` change followed in TYP-60 (actually consumed there).
- **Implementation**: two SQL constants per repo (with/without distance/q). Cleaner than conditional WHERE — readable, planner optimizes each branch.
- **Unblocked**: TYP-60 (Profile Saved list — shipped same week) and Search-tab nearby-only empty state (TYP-29-ish, future).
- **Design choice**: alphabetical sort when no lat/lng. Save-recency sort deferred (no `saved_places.created_at` column; would need migration).

### 2026-05-13 — TYP-59 merged: Profile Outings list populated

- **Merged in PR #24** (commit `d863ed0`). Branch `typ-59-ios-profile-outings-list-populated`.
- iOS `ProfileView` Outings tab populated. Parallel to TYP-58's Places work — same tri-state rendering, same `scorePill` reuse, same orange-tint 32pt icon block (calendar icon for outings).
- **Client-side filter**: `outing.status == "completed" && outing.finalRating != nil`. **Sort**: by `finalRating DESC` (matches Places list; originally specced as `completedAt DESC`, switched mid-session for consistency).
- Row contents: rank + calendar icon + title + "N stops · weekday, month day" meta + tier-coloured score pill (reuses TYP-58's 6.7/3.4 thresholds).
- `loadOutings()` calls `GET /me/outings` (TYP-19, already shipped). Two loaders fire in parallel via `async let`; TYP-60 added a third (saved places).
- Seed script: 3 sample outings inserted (Friday Brewery Night 8.7, Saturday Day Out 9.2, Coffee & Drinks 7.5), idempotent on `(creator_id, title)`. Each has 2 stops linking to seeded places via `events` rows with `weight=0.5`.
- **Attendee names ("with John, Mike") deferred** — needs backend hydration of `event_invitations` or `outing_invitations`. Separate future ticket.
- **Cleanup ticket TYP-64 filed**: extract `ScorePill` + `CategoryIcon` once a 3rd consumer needs them (Feed or Search). Rule of three.

### 2026-05-12 (later) — TYP-63 merged: README cleanup

- **Merged in PR #23** (commit `9252178`). Branch `typ-63-readme-cleanup-align-with-current-stack-workflow`.
- Root `README.md` had drifted: claimed Fly.io/Railway deploy (actually Render), "Supabase or Clerk" auth (locked to Supabase since TYP-26), `.ics via Resend/SendGrid` as live stack item (v1.1 visual stub), branch strategy out of sync with actual `main`-targeting workflow.
- Cleanup: tech stack updated to reflect Render + Supabase only; getting-started gained an iOS section; branch strategy rewritten to match reality (PRs → `main`); "Two ML Systems" reworded as forward-looking (stubs in v1); pointers to `CLAUDE.md` and `docs/CURRENT_HANDOFF.md` added.

### 2026-05-12 — TYP-58 merged: Profile Places list populated

- **Merged in PR #22** (commit `2b32b74`). Branch `typ-58-ios-profile-places-list-populated`.
- **Backend hydration**: `GET /me/place_ratings` now returns `place_name` and `category` joined from `places`. Same flat-field + `from_attributes=True` pattern as `feed_saves`. Schema (`PlaceRatingOut`), repository (`list_by_user`), and route changed. No migration.
- **iOS Profile Places tab populated**: tri-state rendering (`nil` = ProgressView, `[]` = existing empty state, populated = ranked list). Ranked rows show rank # + 32pt icon-on-tint placeholder + name/category + tier-colored score pill. Pull-to-refresh added.
- **Tier-coloured score pills locked** at thresholds 6.7 (green, "fun") and 3.4 (amber → red). Chosen by Alan as cleaner thirds of 0–10; supersedes the §4 spec's 7.0 / 4.0 boundaries for visual purposes. Backend tier ranges in the comparison algorithm (TYP-45) stay 7.0–10.0 / 4.0–6.9 / 0.0–3.9 — different concern.
- **Dev seed script**: `backend/scripts/seed_dev_data.py` inserts the Figma's 5 Boston places + ratings + (idempotently) patches the user's `display_name` away from the auto-provisioner's email-prefix fallback. Safety rail refuses to write to non-local DBs without explicit `yes`.
- **Local dev loop documented**: simulator-loopback bug on some Xcode versions worked around by binding uvicorn to `0.0.0.0` + pointing `Local.xcconfig` at the Mac's LAN IP. `Local.xcconfig` MUST NOT be committed with the LAN IP — break for Render builds and other devs.
- **Next**: TYP-59 (Outings list) is the natural follow-up. TYP-60 (Saved) blocked on TYP-47, TYP-62 (friends count) blocked on TYP-43, TYP-61 (settings sheet) standalone.
- See `docs/TYP_58_HANDOFF.md` for the full per-ticket breakdown.

### 2026-05-11 — TYP-38 slice 1 merged: Profile empty state + CTA tab switching
- **Profile tab empty state shipped**: identity block (orange initials avatar + name + bio placeholder), `0 friends` card, 3-tab strip (Places / Outings / Saved with zero counts), per-tab empty cards routing to Search / Plan / Search respectively. Temporary Logout button still at bottom — moves to gear sheet later.
- **New `TabSelectionStore` introduced** at `ios/TypeA/TypeA/TabSelectionStore.swift` — `@Observable` class holding the active `AppTab`, injected at app root the same way as `AuthStore`. `MainTabView` binds it into `TabView(selection:)` for two-way sync with the bottom tab bar. Any view can write `tabSelection.current = .search` to switch tabs. Reuse for future cross-view shared state (FriendsStore, FeedStore, etc.) before reaching for `@AppStorage` or singletons.
- **Empty-state copy locked** (in TYP-38 ticket + per-ticket handoff): Places → "Click Search and rate your first place!" / Outings → "Plan your first outing and rate it!" / Saved → "Search and save a place you want to go!".
- **New docs**: `docs/TYP_38_HANDOFF.md` (per-ticket status + remaining slices), `docs/TAB_SWITCHING_UNDERSTANDING.md` (plain-language explainer of the Observable + Environment pattern with stadium scoreboard analogy).
- **TYP-38 NOT closed** — populated Places/Outings/Saved lists, real friends count (needs TYP-43), and settings sheet (separate follow-up ticket) still ahead. Recommended next slice: populated Places list (`GET /me/place_ratings` from TYP-21 already works).
- **Out of session** (locked 05-09 but worth surfacing again): all 10 §7 open questions from `docs/05-09_HANDOFF.md` resolved. Path B for Plan creation (client-side state until Continue, TYP-46 cancelled). Re-rating overwrites. Re-tier warns. Comparison ranking uses pure binary search.

### 2026-05-08 — TYP-10 merged: 4-tab shell shipping
- **TYP-10 merged**: `TabView` with 4 tabs (Feed / Plan / Search / Profile). All wired through `RootView → MainTabView` when authenticated.
- **MainView lifted into `ProfileView`** — greeting + email + logout now live in the Profile tab. `MainView.swift` deleted.
- **Each tab wraps its own `NavigationStack`** so push history is independent per tab; bottom bar persists across pushes within a tab.
- **Feed / Plan / Search show "Coming soon" empty states** styled per design system (orange icon-in-circle + rounded title + secondary subtext). Real content arrives in per-tab content tickets.
- **Tab icons shipped**: Feed = `newspaper`, Plan = `calendar`, Search = `magnifyingglass`, Profile = `person.circle` — matches the 05-07-later mockup decision.
- See `docs/TYP_10_HANDOFF.md` for the SwiftUI mechanics walkthrough (TabView, `.tabItem`, NavigationStack-per-tab, view lifecycle).

### 2026-05-07 (later) — Feed and Plan flow mockups locked

#### Feed tab — final design
- **Trending rail always shows** above the friend feed, even when user has zero friends. Beli-style "app feels alive on day one." Path A (full-screen empty state) rejected.
- **Day-1 commitment**: trending data must be **manually seeded** before alpha launch. With 5–10 friends on TestFlight, organic trending data won't materialize. Pick ~5 Boston spots, insert into `places`, have `/me/trending_places` query pull from them. ~1–2 hour seed task. Add to Linear before TYP-31 (TestFlight).
- **Empty state lives inside the feed section only** — friendly inline card with "No friends yet · Add friends to see what they're rating, saving, and planning" + orange Add friends button. Trending rail above stays unaffected.
- **Trending card visuals**: icon-on-orange-gradient placeholder for v1 (golf, cocktail, beer icons). Google Places photos are **v1.1, NOT v1**. Forward-compatible — swap the `<div class="trend-img">` contents later, layout doesn't change.
- **Brand mark**: star-with-A logo + "TypeA" wordmark in SF Pro Rounded. Header has bell top-right with red unread dot.
- **Tab bar icons**: Feed = page-with-lines (`newspaper`), Plan = `calendar-event`, Search = `magnifyingglass`, Profile = `person.circle`. Active tab uses `FF9F1C` orange. (Resolves the "iOS tab bar styling" open decision.)
- **Activity row pills are color-coded** by type: light orange (`#FFF4E5` / `#B86E0E`) for ratings, gray (`#F2F2F7` / `#3c3c43`) for saves, amber (`#FFE9CC` / `#8B4F0A`) for outings. Faster row-type recognition for a swipe-fast feed (TypeA is closer to Twitter-stream than Beli-list).

#### Plan tab — full creation flow locked
Mockup covers 6 snapshots: empty Plan tab → New event modal → New outing modal (after +Add stop) → Review → Confirmed → populated Plan tab.

- **`Plans | History` segmented toggle** inside the Plan tab — NOT a 5th top-level tab. (4-tab structure stays locked.)
- **Empty state CTA**: orange pill button "Create your first plan" with subtle drop shadow (only place in design system that uses a shadow — first-time visibility justifies it).
- **Modal title flips on stop count**: "New event" with 1 stop → "New outing" with 2+ stops. Matches backend's event-vs-outing model. Adding a 2nd stop also reveals an outing-title field at the top.
- **Both event AND outing modals include the same fields**: place(s), When (scheduled_for), Going (you + Invite friends button), with a Continue button at the bottom. Outing modal additionally has the title field and shows stops as reorderable cards (drag handles visible — see "deferred features" below).
- **Modal flow uses "Continue" (not "Confirm") at editing-stage bottoms.** "Confirm" is reserved for the final lock action on the Review screen. Verbs differentiate stages.
- **Review screen** = post-Continue preview: photo card with right-arrow + paging dots if outing, place name + category subtext below, time meta row, "Get calendar invite" button (visual stub — see below), Going section with invitees + Invite friends button, top-right pencil to return to editing, "Confirm plan" button at bottom locks it.
- **Confirmed snapshot** = Review screen minus pencil minus bottom Confirm button, plus a green "Confirmed" lock badge at top. Green is system success color, not orange — orange stays accent-only.
- **Populated Plan tab** has a `+` button top-right (orange filled circle) to create another plan. Plan cards show photo placeholder + title + meta line ("2 stops · Fri Nov 7 · 7:00 PM") + status badge (green Confirmed / orange Planning) + stacked mini-avatars of invitees.

#### Visual stubs in v1 (NOT real integrations)
- **"Get calendar invite" button**: visible in Review and Confirmed snapshots. v1 shows a "Coming soon" toast on tap. v1.1 ships actual `.ics` generation + email delivery via Resend/SendGrid. Reserves UI real estate so v1.1 doesn't redesign.
- **Photo placeholders everywhere** (trending cards, plan cards, review/confirmed photo block): icon-on-orange-gradient. v1.1 swaps in Google Places photos with attribution. Swap doesn't change layout.

#### New tickets implied by these decisions (not yet filed in Linear)
- **Backend: `GET /me/trending_places` + alpha seed data** — drafted in 05-07 morning entry; today's decisions confirm the seed-script piece is required, not optional.
- **Backend: invitation creation hookup** — Plan-creation flow's "Invite friends" button needs to POST to TYP-20's invitation endpoints. Wire-up ticket.
- **iOS: Plan tab + creation modal** (this mockup is the spec). Estimated ~14–18 hrs given multi-stage modal + form state management. Depends on TYP-10. Should reference this section + the mockup.
- **iOS: Feed tab UI** (TYP-23 backend already done, mockup is the spec). ~10 hrs. Depends on TYP-10.
- **v1.1: calendar invites (.ics + email)** — full ticket: Resend or SendGrid signup, sender domain config, .ics generation, attach to invitation emails. ~10–14 hrs.
- **v1.1: Google Places integration** — API key + billing, photo URL caching strategy, attribution UI. ~12–16 hrs.

#### Deferred features within Plan flow (v1.x, not v1)
- **Drag-to-reorder stops**: drag handles render in mockup (`grip-vertical` icon) but actual SwiftUI drag is non-trivial. v1 ships with delete + re-add. v1.1 adds drag.
- **Outing arrow on photo card**: visible in mockup but `pageTabViewStyle` swipe-through can be deferred — v1 can ship a static photo of stop 1 only if needed for time.

#### Resolves / closes
- ✅ "iOS tab bar styling" open decision → settled with the icons listed above
- ✅ "Brand mark in top nav" open decision → wordmark + small star-A logo together (not either/or)

### 2026-05-07 — Tabs locked + Feed/Search rails defined
- **4 tabs locked**: `Feed / Plan / Search / Profile`. Friends and your-own-activity-log are sub-screens of Profile, not tabs. Memory: `project_ios_tabs.md`.
- **Tickets renamed/rescoped**: TYP-28 from "Friends tab" → "Friends list, add friend, requests" (sub-screen). TYP-30 from "Activity tab" → "Your activity log" (sub-screen). TYP-10 description updated to reflect 4-tab list.
- **4 new per-tab content tickets drafted** in Linear: iOS Feed tab / iOS Plan tab / iOS Search tab / iOS Profile tab root. All depend on TYP-10.
- **Feed gets a "Trending this week" rail** at the top — popular places by friend-graph activity. Pure social signal, no ML.
- **Search gets a "Recommended for you" rail** at the top (when search field is empty) — top 10 places by predicted score for current user. Graceful degradation: <5 ratings → popularity fallback; 5–20 → category-bias; 20+ → real ridge regression.
- **2 new backend tickets queued**: `GET /me/trending_places` and `GET /me/recommendations`. Both small SQL/service work; recommendations endpoint ships v1 with popularity fallback (no real ML required).
- **Google Places stays in scope** but deferred to medium-term. MVP/alpha runs on manually-seeded local `places` table.

### 2026-05-06 — TYP-26 merged + design system locked
- **TYP-26 merged**: full email/password auth flow. Login + Signup + Logout + display_name PATCH /me. Token refresh handled transparently by Supabase SDK. App-launch session bootstrap with `!isExpired` check.
- **iOS design system locked**: `FF9F1C` orange accent (only), iOS system colors for everything else, rounded SF Pro for hero type, 24pt page padding, 12pt corner radius, conversational microcopy. Memory: `project_design_system.md`.
- **`MainView` is a placeholder**, gets lifted into the Profile tab in TYP-10. Then deleted.
- **Per-ticket handoff renamed** for consistency: `IOS_FOUNDATION.md` → `TYP_25_HANDOFF.md`. New: `TYP_26_HANDOFF.md`.

### 2026-05-05 — TYP-25 merged + iOS-first sequencing
- **TYP-25 merged**: Xcode project, APIClient (singleton + async/await + JSON decode), KeychainStore wrapper, Codable models for User/Place/Event/Outing/Friend/FeedItem (discriminated enum). `/health` button proves end-to-end against deployed Render.
- **iOS sequencing decided**: TYP-25 → TYP-26 → TYP-10 → 27 → 28 → 29 → 30 → 31. Auth first, then tab shell, then per-tab content.
- **Prediction UX = single number** ("Recommended Score: 8.9"). No confidence intervals in v1. Memory: `project_prediction_ux.md`.

### 2026-05-04 — Stub /predict endpoints + iOS-first reframe
- **TYP-33 merged**: `GET /places/{id}/predict` and `GET /outings/{id}/predict` return `{"score": 7.5, "model_version": "stub-v0"}`. Auth required, 404 on missing IDs, no ownership check on outing predict.
- **Sequencing reframe**: ML implementation deferred until iOS ships real ratings. iOS-first; ML kicks in once there's data. Memory: `project_ios_first_sequencing.md`.

### Earlier — Foundations
- **TYP-24**: backend deployed to Render. Free-tier gotchas (no pre-deploy command, file-based Python pin, `+psycopg` URL prefix). Memory: `project_render_deploy.md`.
- **TYP-23**: friend feed (`GET /me/feed`) — cursor pagination, discriminated `FeedRatingOut | FeedSaveOut | FeedOutingOut` items.
- **TYP-22**: friendships — Option A schema (1 row pending / 2 rows accepted), 6 endpoints.
- **TYP-21**: ratings — `place_ratings` append-only with DISTINCT ON dedupe, `outings/{id}/rate` with per-event weights.
- **TYP-20**: invitations — bulk invite, `/me`-scoped RSVP, embedded resource on incoming list, creator auto-RSVP retrofit.
- **TYP-19**: events + outings — 16 endpoints, full lifecycle with confirm/unconfirm/cancel cascades.
- **TYP-18**: places search — earthdistance + pg_trgm extensions, raw `text()` SQL.
- **TYP-17**: auth foundation — `/me` endpoints, Supabase JWT validation, JWKS-cached.
- **TYP-8 / 16**: schema + Alembic.

---

## Current state

### Backend
- **Deployed** at `https://type-a-api.onrender.com` (Render free tier, cold starts ~30–60s)
- **30+ endpoints** across users, places, events, outings, ratings, friendships, invitations, feed, predictions (stub)
- **Auth**: Supabase JWT (ES256, JWKS-verified), auto-provisioning on first `/me` hit
- **DB**: PostgreSQL with extensions `cube`, `earthdistance`, `pg_trgm`
- **ML**: stubs only — `/predict_place` and `/predict_outing` return constant 7.5
- **Pending tickets**: `/me/trending_places` (with manual alpha seed script), `/me/recommendations`, invitation hookup for Plan creation flow (drafted, not yet filed in Linear)

### iOS
- **Auth flow shipping**: login, signup with display_name, logout, app-launch session bootstrap
- **Design system applied** to all 3 screens (Login, Signup, MainView)
- **Networking**: APIClient with async/await, JSON encode/decode, generic typed responses, bearer auto-attach via Supabase SDK
- **Feed and Plan mockups locked** as of 2026-05-07. Use them as spec for the per-tab tickets.
- **4-tab shell shipping** (TYP-10) — Feed/Plan/Search show "Coming soon", Profile is fully functional with greeting + email + logout.
- **Pending**: 4 per-tab content tickets + TYP-27/28/29/30 sub-screens + TYP-31 TestFlight

### ML
- **Schema ready**: `outings.derived_score` (frozen at confirm), `attribution_outputs.attributed_effect` (per-user per-place), `events.weight` (per-stop slider)
- **mvML path active** (since 2026-08-19) — supersedes the earlier "wait for real rating data" sequencing. Synthetic training data is seeded and the models train against it now.
- **Training data shipped** (TYP-69): 168 synthetic ratings + 40 weighted 2-stop outings across 8 preference personas, generated from a `PREFERENCE_MATRIX` answer key in `backend/scripts/seed_ml_data.py`.
- **Next**: TYP-70 (Atomic Recommender, ridge) → TYP-71 (Attribution Model, hierarchical) → TYP-72 (iOS Recommended Score). `/places/{id}/predict` and `/outings/{id}/predict` are still `stub-v0` returning 7.5.
- Recommendations endpoint will still use popularity-fallback in v1.

### Design
- **TYP-34** in progress (Figma wireframes for Plan tab / homepage)
- **Feed mockup locked** — Trending rail + friend feed list, Path B empty state, three-color pills, star-A logo, fixed tab icons.
- **Plan flow mockup locked** — 6 snapshots: empty → New event → New outing → Review → Confirmed → populated. Calendar invite + photos are visual stubs in v1.

---

## Active questions / open decisions

- **Recommendations endpoint exclusions**: should it exclude places the user has already rated? Already saved? (Lean: exclude already-rated, include saved. Saves are aspirational, ratings are tried-and-judged.)
- **Plan modal: separate "Continue → Review" pattern, or single-screen with inline confirm?** Mockup uses two-stage (Continue then Confirm). Pro: cleaner mental model — editing vs reviewing. Con: extra tap. iOS convention supports both.
- **`POST /events/{id}/promote_to_outing`** is currently stubbed at 501. The Plan creation flow's "Add stop" button needs this to actually work — OR the iOS client builds the outing client-side and POSTs as outing-with-events from scratch. Pick a path before TYP-19a / Plan UI ticket.

---

## Pointers — where to look

- **Per-ticket deep-dives**: `docs/TYP_25_HANDOFF.md`, `docs/TYP_26_HANDOFF.md`, `docs/TYP_10_HANDOFF.md`
- **Endpoint catalogs**: `docs/RATING_ENDPOINTS.md`, `docs/FRIENDSHIPS_ENDPOINTS.md`
- **Architectural understanding**: `docs/JWT_AUTH_UNDERSTANDING.md`, `docs/ML_RATING_UNDERSTANDING.md`, `docs/ALEMBIC_NOTES.md`
- **Project conventions**: `CLAUDE.md` (root)
- **Memory** (across sessions): `MEMORY.md` index in user's auto-memory folder