# Design Handoff — 2026-05-09 Session

Written for Claude Code (with Linear MCP) to ingest and file tickets from. Covers four full mockup sessions: Feed tab, Plan creation flow, Search + Comparison ranking, and Profile tab + friend-button states.

This document is the **product spec**. Figma covers the visual spec separately. When in doubt, this doc wins on behavior; Figma wins on pixel-level styling.

---

## Reading guide

- **§1 — Design system reaffirmed.** Color, typography, components.
- **§2 — Feed tab.** Locked design + empty state.
- **§3 — Plan tab + creation flow.** 6-snapshot flow.
- **§4 — Search tab + Beli-style comparison ranking.** Scoping bombshell here — this is the biggest scope-add of the session.
- **§5 — Profile tab.** 4 snapshots + friend-button state machine.
- **§6 — Tickets to file.** Concrete list, broken by category, ready to file in Linear.
- **§7 — Open questions / decisions still owed.** Things that need Alan to decide before tickets can ship.
- **§8 — Updated v1 scope and timeline reality.**

---

## §1 — Design system reaffirmed

The 2026-05-06 design lock from `project_design_system.md` memory holds. Reaffirming what got applied this session:

- **Accent**: `#FF9F1C` (warm orange). Only accent color. No blue, no teal, no mint.
- **Typography**: SF Pro Rounded for hero/title text (bold/semibold, 18–32pt). Regular SF Pro for body. Subtitles in `.secondary` gray.
- **Page padding**: 24pt horizontal (16pt in tighter sub-views like modals).
- **Corner radius**: 12pt for cards/buttons, 10pt for inputs and pills.
- **Tabbar icons (locked)**: Feed = `newspaper`, Plan = `calendar-event`, Search = `magnifyingglass`, Profile = `user-circle`. Active tab uses orange.
- **Brand mark**: orange star with black "A" + "TypeA" wordmark (single word). No teal background. Used in Feed top-left header.

System colors used freely for everything except accent — `.primary` text, `.secondary` text, `secondarySystemBackground`, etc. Status colors: green for success/confirmed, red for destructive, yellow/amber for caution. Orange stays reserved for the brand accent and active states.

---

## §2 — Feed tab

### Layout (top to bottom)

1. **Header row**: brand mark (star+wordmark) top-left, bell icon top-right with red unread dot when notifications exist
2. **"Trending this week" section title** with flame icon
3. **Horizontal scrolling rail** of trending place cards
4. **"Your feed" section label** (small caps, gray)
5. **Friends' activity rows** — vertical scroll

### Trending cards

- **Always shown**, even when user has zero friends. Path B (Beli-style) chosen over Path A (full-screen empty).
- **Width**: ~140pt per card, scroll horizontally
- **Top half**: photo placeholder — icon-on-orange-gradient (`#FFE9CC` → `#FFD49B`). Icon represents place category (golf, cocktail, beer, pizza, etc.).
- **Bottom half**: place name (semibold), category (gray), social count (orange) e.g. "8 friends" or "Popular" if no friends yet.
- **Photos are v1.1**, not v1. Layout supports drop-in replacement later — swap the gradient div for an `AsyncImage`. No layout change.

### Activity rows (3 types)

All three types share row layout:
- 42pt circular initials avatar (no photos in v1)
- Name (semibold) + verb + place name (semibold) — sentence form
- Below: colored pill + relative timestamp + chevron

**Pill colors differentiate row types** (Alan's call: speed-of-recognition matters more than visual quietness):
- **Rating** rows: light orange pill `#FFF4E5` bg / `#B86E0E` text, star icon, score (e.g. "8.4")
- **Save** rows: gray pill `#F2F2F7` bg / `#3c3c43` text, bookmark icon, "Saved"
- **Outing** rows: amber pill `#FFE9CC` bg / `#8B4F0A` text, map-pin icon, score

### Empty state (Path B)

When the user has zero friends:
- Trending rail still renders fully
- "Your feed" section label still shows
- Below that label: an inline empty card (not a full-screen empty state)
  - Soft-orange dashed-border box (`#fafafa` bg, dashed `rgba(60,60,67,0.22)` border, 14pt radius)
  - Centered content: small orange-bg icon circle (users icon), "No friends yet" title, "Add friends to see what they're rating, saving, and planning." subtext, orange CTA pill "Add friends"

### Cold-start commitment

Trending is always-shown only because Alan committed to **manually seeding ~5 Boston places** before alpha launch. Without seed data, trending would be empty for the first ~30 days of TestFlight (alpha cohort = 5–10 NU friends; not enough to drive organic trending). Seed task is part of the trending endpoint ticket.

### Implementation notes

- Backend already exists: `GET /me/feed` (TYP-23) for activity rows. Cursor pagination on `created_at`. Three-shape discriminated union response.
- Backend NEW: `GET /me/trending_places` returns top N places ordered by rolling-window friend-graph activity count. Falls back to global popularity when friend count is low.
- iOS uses `Models.swift`'s `FeedItem` discriminated enum already (TYP-25).

---

## §3 — Plan tab + creation flow

### Plan tab layout

- **Header**: "Plan" title (left), `+` button (orange filled circle, right) — only visible when there's at least one plan
- **Segmented toggle**: `Plans | History` — *inside* the Plan tab, NOT new bottom tabs. Plans = current/upcoming, History = past completed/cancelled
- **Body**: list of plan cards

### Plan card layout

- 16:9 photo placeholder header (icon-on-orange-gradient, same pattern as trending cards)
- Title (e.g. "Friday w/ the crew")
- Meta line: "2 stops · Fri Nov 7 · 7:00 PM" or "Bar Lyon · Sat Nov 8 · 8:00 PM" for single-event plans
- Footer row: status badge (left), stacked mini-avatars of invitees (right)
- Status badge colors: green `Confirmed` (check icon), orange `Planning` (edit icon), gray `Completed` (check), red `Cancelled` (x). Cards in `Planning` state render at 0.7 opacity to visually de-emphasize.

### Empty state

First-time user has zero plans:
- Centered orange-bg icon circle (calendar-plus icon)
- "No plans yet" (rounded font, 16pt semibold)
- "Plan a night out and predict how much you'll enjoy it." (subtext)
- **Pill-shaped CTA**: "Create your first plan" — orange filled, with a soft drop shadow `0 2px 8px rgba(255,159,28,0.3)`. The drop shadow is the *only* place in the design system that uses one. First-time visibility justifies it.

### Creation modal — full slide-up sheet

Modal slides up from bottom, takes most of the screen (top: 36pt of black phone frame visible above modal). Modal has rounded top corners (18pt radius), drag handle at top, header row, body, footer with primary action.

**Header row**:
- Left: "Cancel" or "Close" or "Done" depending on stage (text link in orange)
- Center: stage title — "New event" / "New outing" / "Friday w/ the crew" depending on stage
- Right: optional pencil icon (review state) or empty (other states)

**Stage 1: Editing — single event**
- Modal title: "New event"
- Place selector input (place icon + "Top Golf" + "Activity · Boston")
- "+ Add stop" dashed-border orange button (1.3px dashed `rgba(255,159,28,0.5)`)
- "When" — calendar input showing scheduled datetime
- "Going" — list of invitees (creator pre-filled with "(you)" tag) + "Invite friends" dashed gray button
- Footer: "Continue" button (orange filled, 11pt radius)

**Stage 2: Editing — outing (after +Add stop)**
- Modal title flips to "New outing"
- New "Outing title" input appears at top with pencil icon, placeholder "Friday w/ the crew"
- Stops list now shows reorderable cards (vertical drag handles `grip-vertical` icon visible) — "Stop 1", "Stop 2"
- "+ Add stop" stays
- "When", "Going", "Invite friends" same as Stage 1
- Footer: "Continue"

**Stage 3: Review (after Continue)**
- Modal title shows the outing title
- Right header icon: pencil button (gray pill) — tapping returns to Stage 2 editing
- Body:
  - Photo card (16:10 ratio, icon-on-gradient placeholder). If outing, right-arrow chevron + paging dots overlay so user can swipe through stops.
  - Place name + category subtext (subtext changes as user swipes through stops)
  - Time meta row (clock icon + "Fri Nov 7 · 7:00 – 9:00 PM")
  - **"Get calendar invite" button** — this is a v1.1 visual stub. v1 shows "Coming soon" toast on tap.
  - "Going" section with invitees + Invite friends button (same as editing stages)
- Footer: "Confirm plan" button (orange filled)

**Stage 4: Confirmed (locked)**
- Modal title shows the outing title
- Header: "Done" link left, no pencil right
- Body shows green "Confirmed" lock badge above the photo card (`#E8F8EE` bg, `#1F8A3F` text, lock icon, 8pt radius)
- Photo + place + time + calendar invite + invitees same as Stage 3
- "Going · 3" header on invitees once friends are added
- **No bottom Confirm button** — locked state has no further action
- Tapping "Done" dismisses modal, returns to Plan tab where the new card is visible

### Architecture decision still owed

The `promote_to_outing` endpoint (TYP-19) is currently stubbed at 501. The Plan modal transitions between "event" and "outing" titles client-side as the user adds stops. **Two paths to handle this** — pick one before iOS Plan UI ticket starts:

- **Path A**: Ship TYP-19a (real `promote_to_outing` endpoint). iOS POSTs an event, then on Add stop calls promote, then POSTs the second event with `outing_id`. More backend work but mirrors user flow.
- **Path B (recommended)**: Client-side state until Continue. iOS holds the whole plan in memory while editing. On Continue, decides POST event vs POST outing-with-events from scratch. No new backend work.

Most teams pick B. Decision needed before iOS Plan UI ticket can spec correctly.

### v1.1 visual stubs in this flow

- **"Get calendar invite" button**: visible in Review and Confirmed. v1 shows toast. v1.1 ships .ics generation + email delivery (Resend or SendGrid). UI exists for forward compatibility.
- **Photo placeholders everywhere**: same pattern as Feed/trending. v1.1 swaps in Google Places photos.
- **Drag-to-reorder stops**: drag handles render but functionality deferred. v1 ships with delete + re-add only.
- **Outing photo paging** (right-arrow + dots): renders visually; v1 can ship static stop-1-only if needed for time.

---

## §4 — Search tab + Beli-style comparison ranking

This is the biggest scope-add of the session. **Alan picked Path B (full Beli-style comparisons in v1) with eyes open** after being shown the cost.

### Search tab layout

- **Header**: "Search" title only
- **Search bar** (pinned below header): pill-shaped, gray bg `#F2F2F7`, search icon + "Search places…" placeholder
- **Section label**: "NEARBY PLACES" (uppercase, small caps, gray) with map-pin icon in orange
- **Vertical scrolling list of place rows**

### Place row

- 38pt rounded square photo placeholder (icon-on-orange-gradient)
- Name (semibold, 12pt) + meta line "Activity · 0.4 mi" (10pt gray)
- **Three action icons** stacked horizontally on the right:
  - **Save** (bookmark icon) — gray bg `#F2F2F7`, gray icon. When saved, icon becomes filled orange. Toggles via `POST/DELETE /saved_places/{id}`.
  - **Rate** (star icon) — gray bg, gray icon. When rated, icon becomes filled orange. Tapping opens the comparison ranking flow (see below).
  - **Plan** (calendar-plus icon) — **orange filled bg**, white icon. The "money button" of the row — kicks user out of search into Plan creation modal with this place pre-filled. Higher visual weight than save/rate because it's the primary discovery-to-action handoff.

### Distance display

Requires CoreLocation permission (iOS) + lat/lng on `GET /places` request. Backend already supports this via TYP-18 `earthdistance`. iOS adds: location permission prompt at first Search-tab entry, falls back gracefully if denied (drops "0.4 mi" from rows, sorts by name).

### Tapping a row (not an icon)

Opens a **place detail screen** — new ticket (~8 hrs iOS work). Out of scope for the Search tab itself but blocks iOS Search ticket.

### Tab content

When search field is empty: show "Nearby places" list (default).
When search field has text: list filters/replaces with search results from `GET /places?q=...`.

**No "Recommended for you" rail** in v1 — user explicitly de-scoped. Reasoning: rec rail needs ratings to compute against, and ratings only exist after users start using the app. Ships in v1.x once data exists.

---

### Beli-style comparison ranking flow

Tapping the **rate (star)** icon on any place row triggers this multi-screen flow.

#### Snapshot 1 — Tier prompt (centered card modal)

- **Centered card**, NOT a full-height slide-up. Search screen visible behind, dimmed via `rgba(0,0,0,0.5)` overlay. Card has 18pt radius, `0 10px 40px rgba(0,0,0,0.2)` shadow.
- Top-right of card: small gray X close button
- Title (rounded font, 18pt semibold): "How was Top Golf?"
- Subtext: "Pick a vibe — we'll fine-tune next."
- **Three tier buttons** stacked, full-width:
  - **"It was fun"** — green border `#34C759`, green text `#1F8A3F`, soft green tint bg
  - **"It was okay"** — amber border `#E0A800`, amber text `#8B6914`, soft amber tint bg (NOT yellow `#FFCC00` — too cheerful)
  - **"It wasn't fun"** — red border `#FF3B30`, red text `#C62828`, soft red tint bg
- **No emoji** (Alan's call). Text + traffic-light colors do the work.

#### Snapshot 2 — First comparison

- Same centered card pattern. Search screen visible behind.
- Top of card: "1 OF 4" progress label (uppercase small caps, gray)
- Top-right: X close button
- Title (rounded, 16pt semibold): "Which did you like more?"
- Subtext: "Top Golf vs. one you've already rated"
- **Two place cards side-by-side** with "VS" separator (small gray text):
  - Each card: 50pt circular photo placeholder + place name + category/score
  - The new place (being rated) shows category
  - The existing place shows its current score (e.g. "8.0")
- Tapping a card = picking the winner. Modal advances to next comparison.

#### Snapshot 3 — Mid comparison (representative)

Same as snapshot 2 but progress label is "3 OF 4" and subtext changes to "Almost done — narrowing the score."

#### Snapshot 4 — Final score reveal

- Centered card (no overlay X — terminal state)
- 56pt orange-bg icon circle (golf icon for Top Golf)
- Place name (rounded, 19pt semibold) + category subtext
- **Big orange score circle** (78pt diameter, `#FF9F1C` bg, white text, 26pt rounded bold "8.4")
- Below score: tier badge — `It was fun` in green pill (`rgba(52,199,89,0.12)` bg, `#1F8A3F` text)
- Footer: "Done" button (orange filled, full-width)

### Algorithmic / backend implications

This flow is NOT free. Implementing it requires:

1. **`POST /comparisons` endpoint** — submit "user prefers A over B" results. Schema already exists (`comparisons` table, polymorphic `place|outing` type). No endpoint exists yet.

2. **Pairing algorithm** — given a new place to rank in a tier, which existing place to compare against? Standard approach: binary-search through the user's existing places-in-this-tier sorted by score. log₂(N) comparisons.

3. **Scoring algorithm** — combine tier midpoint + comparison wins/losses → final 0.0–10.0 score. Tier score ranges: Liked = 7.0–10.0, Okay = 4.0–6.9, Didn't like = 0.0–3.9. Where in the tier the new place lands depends on its comparison results.

4. **Edge cases (must be in spec)**:
   - **First-ever rating**: 0 prior places to compare against. Skip comparisons entirely. Store tier midpoint (e.g., Liked → 8.5, Okay → 5.5, Didn't like → 2.0).
   - **One prior rating in same tier**: 1 comparison max. Score lands above or below the existing one's score.
   - **N prior ratings**: ceil(log₂(N)) comparisons.
   - **Re-rating**: user re-rates a place they've already rated. Path forward: (a) overwrite by re-running comparison flow, OR (b) preserve old rating and add a new one (current `place_ratings` schema is append-only with DISTINCT ON dedupe — TYP-21). Recommendation: (b) — append, dedupe at read time. Keeps history.
   - **Re-tiering**: user previously rated as "Okay", re-rates as "Liked". The new rating is in a different tier; comparison flow runs against that tier's existing places.

5. **iOS state machine** — comparison loop manages: current opponent, comparison count remaining, results so far. On final tap, POSTs all comparison results + tier choice + place_id to backend. Backend computes final score and writes to `place_ratings` and `comparisons` tables atomically.

### Estimated effort

- Backend (endpoints + algorithm + tests): ~14 hrs
- iOS (4 screens + state machine + integration): ~10 hrs
- **Total ~24 hrs** of new work over and above the existing ratings infrastructure.

---

## §5 — Profile tab + friend button states

### Profile tab layout (own profile)

1. **Header row**: empty left (no back button — tab root), gear icon top-right (settings sheet entry point)
2. **Identity block**: 60pt orange initials avatar (left), name + bio (right). Bio placeholder when empty: "Tap settings to add a bio" in italic gray
3. **Friends row**: card-style row with overlapping mini-avatars + "12 friends" + chevron. Tap → Friends sub-screen (lists, add friend, requests). This is TYP-28 territory, now confirmed as a sub-screen of Profile.
4. **Tab strip**: 3 tabs — `Places (count) | Outings (count) | Saved (count)`. Active = orange text + 2pt orange underline. Inactive = gray text. Pattern: standard iOS underline tab strip.
5. **Tab content body**: list view appropriate to active tab.

### Tab content per tab

- **Places tab**: Beli-style ranked list of rated places. Each row: rank number (1, 2, 3…) + 32pt photo placeholder + place name + category + score (orange, rounded bold). Sorted by score descending.
- **Outings tab**: list of completed outings (TBD layout — likely similar to Plan card but read-only with rating displayed)
- **Saved tab**: list of bookmarked places. Each row: 32pt photo placeholder + place name + category/location + filled orange bookmark icon (rightmost, decorative).

### Empty states per tab

Each tab has its own empty state when count is 0:
- **Places empty**: small orange icon (star) + "No places yet" + "Rate places you've been and they'll show up here, ranked." + "Find places to rate" CTA → routes to Search tab
- **Outings empty**: similar pattern, routes to Plan tab
- **Saved empty**: similar pattern, routes to Search tab

### Settings sheet (gear icon)

Gear icon top-right opens a settings sheet (modal or pushed view). Sheet contains:
- Edit profile (display_name, bio)
- Logout
- Future v1.x: notifications, privacy, blocked users

### Friend's profile (viewing someone else)

**Differences from own profile**:
- **Top-right empty** (no gear icon) — settings/logout don't apply
- **Top-left has back chevron** (`<`) in orange — pushes back rather than tab-rooted
- **No bio placeholder** — if their bio is empty, just show nothing (don't tell them how to add one)
- **Friend button next to name** — see state machine below
- **Friends row shows "8 friends · 2 mutual"** — mutual count requires new backend work (intersection query). ~30 min ticket.
- **Tab content**: same 3 tabs (Places/Outings/Saved), same layouts. Tap on a place-row in Places does NOT open editing UI — read-only.

---

### Friend button — 3-state UI on profiles

**This is the locked design**. The 4th state ("pending received") is handled exclusively on the Notifications screen, NOT inline on the friend's profile. Alan rejected the dual-path UX (banner + notifications screen).

**State 1 — Add (default, no friendship row exists)**
- Visual: 24pt orange filled circle, white `+` icon
- Action: tap → `POST /friends/requests` creates `(me, them, 'pending')`
- Transitions to State 2

**State 2 — Pending sent (you sent the request)**
- Visual: 24pt white circle, gray border, gray clock icon
- Color choice: gray (not orange) because action is in flight, nothing to do — visual de-emphasis
- Action: tap → confirmation prompt "Cancel friend request?" → if yes, `DELETE /friends/requests/{user_id}`
- ⚠️ **`DELETE /friends/requests/{user_id}` doesn't exist yet.** New backend ticket (rescind endpoint) — see §6.
- Transitions to State 1 if rescinded
- Transitions to State 4 if recipient accepts (via Notifications screen)
- **Auto-accept case**: if the other user has *also* sent you a pending request when you tap `+` (State 1), backend auto-accepts both directions and you skip directly to State 4 — `FRIENDSHIPS_ENDPOINTS.md` documents this. UI snaps to State 4 immediately.

**State 3 — Friends (accepted, friendship exists)**
- Visual: 24pt white circle, orange border (1.5px), orange person-with-check icon (`user-check`)
- Color choice: hollow (not filled) because tapping is *destructive* (unfriend) — Apple convention is to make destructive actions visually quieter
- Action: tap → confirmation dialog "Unfriend Jake? You'll need to send a new request to refriend." → if yes, `DELETE /me/friends/{user_id}`
- Transitions to State 1
- ⚠️ **The confirmation dialog is non-negotiable for v1.** Accidental unfriending is a real failure mode.

**State 4 (was pending received) — handled on Notifications screen, NOT inline**
- When user A sends user B a request, B sees the pending request only in their Notifications/Requests screen
- Visiting A's profile from B's perspective shows... A's profile in State 1 (Add button). If B taps `+` to add A, backend auto-accepts because A already has a pending request to B. Net effect: B can accept A's request either via Notifications OR by visiting A's profile and tapping `+`. Either way, atomic auto-accept.

### Visual treatment of friend button

- Always inline, immediately to the right of the user's display_name (small gap, ~6pt)
- 24pt circle (smaller than action buttons elsewhere — it's a status indicator + secondary action, not a primary CTA)
- Icon size: 12–15pt depending on state
- Tappable area should be enlarged via SwiftUI `.contentShape(Rectangle())` to ~44pt for accessibility — visual size doesn't have to match touch target

---

## §6 — Tickets to file (for Linear MCP)

**File these in Linear, sorted into the categories below.** Reference this doc by date (`Design Handoff 2026-05-09`) in each ticket's description.

### Backend tickets

| Ticket | Estimate | Dependencies |
|---|---|---|
| **Add `bio` field to `users` table** — Alembic migration `bio TEXT NULL`, update `UserOut` and `UserUpdate` Pydantic schemas, ensure `PATCH /me` accepts and persists bio | 1 hr | None |
| **`GET /me/trending_places` endpoint + alpha seed script** — returns top N places by friend-graph activity in last 7 days, falls back to global popularity. Includes a seed script `scripts/seed_alpha_places.py` that inserts 5–10 manually curated Boston spots into `places` table | 3 hrs | None |
| **`POST /friends/requests/{user_id}/rescind` (or `DELETE /friends/requests/{user_id}`)** — allows requester to rescind a pending friend request before recipient accepts/rejects. Currently missing per `FRIENDSHIPS_ENDPOINTS.md`. Hard-deletes the pending row | 1 hr | None |
| **`GET /users/{user_id}` + mutual friends count** — returns user profile data for friend-view. Includes `mutual_friends_count` computed via friendship table intersection. Auth-aware: includes private fields only when user_id == current_user.user_id | 3 hrs | None |
| **Profile counts endpoint** — either inline on `GET /users/{id}` as `{places_rated_count, outings_completed_count, saved_count}` OR a separate `GET /users/{id}/counts`. Powers tab-strip counts on Profile | 1.5 hrs | None |
| **`POST /comparisons` endpoint + scoring algorithm** — accepts list of comparison results + tier choice + new place_id, runs scoring algorithm, writes to `place_ratings` (final score) and `comparisons` (history). Algorithm in `app/services/ranking.py`. Tier midpoints: Liked 7.0–10.0, Okay 4.0–6.9, Didn't like 0.0–3.9. log₂(N) comparisons via binary-search-style pairing | 8 hrs | None — schema already exists |
| **`GET /me/comparison_pairing` (or extend POST endpoint)** — returns next opponent for an in-flight ranking session. iOS calls this between rounds | 2 hrs | Comparisons endpoint |
| **TYP-19a: `POST /events/{id}/promote_to_outing`** — implement the currently-stubbed endpoint. ONLY needed if iOS Plan UI takes Path A. Skip if Path B chosen. | 4 hrs (if needed) | None |
| **`GET /me/saved_places` distance computation already supports lat/lng** — verify TYP-18 endpoint returns distance_m when called from Search tab nearby-places mode (no `q` required) — may need small change to make `q` optional | 0.5 hrs | None |

### iOS tickets

| Ticket | Estimate | Dependencies |
|---|---|---|
| **TYP-10: Tab shell** — already in Linear, scope unchanged. 4 tabs with placeholder views per tab. Lifts existing `MainView` content into the Profile tab | 4 hrs | None (TYP-26 done) |
| **iOS Feed tab** — full implementation per §2. Trending rail + activity rows + Path B empty state. Wires up `GET /me/feed` (TYP-23) and `GET /me/trending_places` (new) | 12 hrs | TYP-10, trending endpoint |
| **iOS Plan tab + creation modal** — full implementation per §3. Empty state + populated card list + 4-stage creation modal (event/outing/review/confirmed) + segmented Plans/History toggle | 18 hrs | TYP-10, promote_to_outing decision |
| **iOS Search tab + nearby places** — search bar + nearby list + 3-icon rows per §4. CoreLocation permission flow. Wires `GET /places?q=&lat=&lng=` (existing TYP-18) | 10 hrs | TYP-10 |
| **iOS comparison ranking flow** — 4-screen flow per §4. Tier prompt → comparisons loop → final score reveal. State machine handles dynamic comparison count (skip when zero priors). Centered-card modal pattern | 10 hrs | Comparisons endpoint, Search tab |
| **iOS Place detail screen** — new screen for tapping a place-row (anywhere — Search, Profile, Feed). Shows place info, user's rating if any, friends who rated/saved, action buttons (save/rate/plan). | 8 hrs | TYP-10 |
| **iOS Profile tab — own profile** — identity block + friends row + 3-tab strip + tab content (Places/Outings/Saved) + empty states + gear icon → settings sheet (Edit profile + Logout). Per §5 | 14 hrs | TYP-10, profile counts endpoint, bio field |
| **iOS Profile tab — friend view** — same screen with auth-scoped variants: hide gear, show back chevron, friend button state machine (3 states + auto-accept handling), mutual friends count display | 8 hrs | Own profile, friend rescind endpoint, GET /users/{id} |
| **iOS Friends sub-screen** — TYP-28 retitled. List of friends + add friend (via search or username) + incoming requests view (where the "pending received" state actually lives) | 10 hrs | Profile tab, friend rescind endpoint |
| **iOS Notifications screen** — list of unread notifications including friend request received, invitation received, etc. Bell icon top-right of Feed routes here. Inline accept/reject for friend requests | 8 hrs | Friends sub-screen |
| **iOS Activity log sub-screen** — TYP-30 retitled. Your own ratings/saves/outings as a feed-style list, filtered to you. Routed from Profile (probably from a "View all" link on each tab? — Alan to confirm) | 6 hrs | Profile tab |

### v1.1 tickets (post-launch, NOT v1)

| Ticket | Estimate |
|---|---|
| **Calendar invite (.ics) generation + email delivery** — Resend or SendGrid signup, sender domain config (DNS work: SPF/DKIM), .ics generation lib, email templates, attach to invitation flow. Wires the "Get calendar invite" button currently stubbed | 12 hrs |
| **Google Places photo integration** — API key, billing setup, photo URL caching strategy (URLs expire), attribution UI (Google ToS requires "Photo by [contributor]" displayed). Replaces icon-on-orange placeholders everywhere | 14 hrs |
| **Search tab "Recommended for you" rail** — top 10 places by predicted score for current user. Graceful degradation: <5 ratings → popularity fallback, 5–20 → category-bias, 20+ → real ridge regression | 8 hrs |
| **Drag-to-reorder stops in outing creation** — SwiftUI drag-and-drop on stop list, persists `events.sequence_position` | 4 hrs |
| **Photo upload for user avatars** — image picker, Supabase Storage upload, cropping UI, caching, fallback to initials when no photo | 8 hrs |
| **Outing photo paging UI** — `pageTabViewStyle` swipe-through on outing review screen so user can preview all stops | 3 hrs |
| **Public profile preview** — let users see what their profile looks like to a friend | 4 hrs |

### Documentation tickets

| Ticket | Estimate |
|---|---|
| **Update `CURRENT_HANDOFF.md`** with all decisions from this 2026-05-09 session — Alan to integrate this doc's decisions into the rolling handoff. Or just append this doc as-is | 0.5 hrs |
| **Memory updates** — extend `project_design_system.md`, add `project_plan_flow.md`, add `project_search_comparison.md`, add `project_profile_structure.md` | 1 hr |

---

## §7 — Open questions / decisions still owed

These need Alan to decide before tickets can be filed cleanly OR before iOS implementation can start.

### Architecture / scope
1. **Promote-to-outing path** (Path A or Path B from §3). Recommendation: B. Decide before iOS Plan UI ticket.
2. **Activity log entry point**: should each Profile tab have a "View all" link that opens an Activity log sub-screen, or is each tab itself the full list? If full list, what does the Activity log sub-screen even show? (Possibly redundant with the 3 tabs.)
3. **Recommendation endpoint exclusions** (carried from prior handoff): exclude already-rated places? Already-saved? Lean: exclude already-rated, include saved.

### UX micro-decisions
4. **Re-rating UX**: when user re-rates a place, do we (a) overwrite old rating by re-running comparison flow, or (b) append new rating, dedupe at read time? Recommendation: (b), matches existing schema.
5. **Re-tiering UX**: if user re-rates and picks a different tier, should the system warn them ("You previously rated this 'Liked'. Are you sure?") or just accept the new tier silently?
6. **Friend confirmation dialogs**: rescind and unfriend both need confirmation dialogs. Standard iOS alert, or custom-styled? Recommendation: iOS standard (`UIAlertController` / `.alert` modifier).

### Product / business
7. **Photo-upload scope** for v1: confirmed deferred to v1.1. But the Profile screen looks visibly empty for a user with default avatar — is the design tolerable for the alpha cohort?
8. **TestFlight readiness gate**: at what point is v1 "ready"? Now that scope has expanded substantially, the original `handoff-05-02.md` definition (5–10 NU friends installed and using) probably needs revisiting. What's the minimum feature set that justifies sending the TestFlight invite?

### Technical
9. **CoreLocation permission timing**: prompt at app launch, at first Search-tab entry, or only when user explicitly searches nearby? Recommendation: at first Search-tab entry, with skippable "Allow location" empty state if denied.
10. **Comparison pairing algorithm choice**: pure binary search, or Elo-style update with random opponent selection? Pure binary search is simpler and what Beli does. Elo is more "ML-flavored" but adds complexity.

---

## §8 — Updated v1 scope and timeline reality

### Net work added in this session (today only)

| Feature | Hours added to v1 |
|---|---|
| Plan creation flow | 18 |
| Search tab + place detail screen | 18 |
| Beli-style comparison ranking | 24 |
| Profile tab (own + friend view) | 22 |
| Friends sub-screen + Notifications | 18 |
| Activity log | 6 |
| Backend for all the above | ~17 |
| **Total this session** | **~123 hrs** |

Plus visual stubs that are NOT in v1 but are mocked:
- Calendar invites: ~12 hrs (deferred)
- Google Places: ~14 hrs (deferred)
- Photo upload: ~8 hrs (deferred)

### Cumulative v1 estimate

`handoff-05-02.md` had v1 at ~175 hrs total (~125 iOS + ~50 backend). After today: **~298 hrs total**. At Alan's stated 6 hrs/day pace = ~50 days of focused work = **~7 weeks calendar minimum**, more likely 8–10 weeks accounting for context switching and learning curve.

**Realistic v1 ship target: late June to mid-July 2026.** Not "ship in a week."

This is fine — Alan explicitly said "no hard deadline, ship when ready" in `handoff-05-02.md`. But the phrase "v1" is now doing a lot more work than it was a week ago. Future Claude sessions should be aware that scope grew substantially on 2026-05-09 and *might* benefit from a re-cut conversation:
- What if comparison ranking is v1.1 instead of v1?
- What if friend-view profile is v1.1 instead of v1?
- What if Activity log sub-screen is v1.1?

If Alan wants to bring back the original "ship in 5 weeks" target, ~70 hrs of work needs to come out. Those three are the natural cut candidates. **Not making the cut now — just flagging that the option exists.**

---

## §9 — Documents this references

- `CURRENT_HANDOFF.md` — rolling handoff (Alan should integrate this doc's decisions)
- `TYP_25_HANDOFF.md` — iOS foundation (APIClient, KeychainStore, Models)
- `TYP_26_HANDOFF.md` — auth flow (login, signup, AuthStore)
- `RATING_ENDPOINTS.md` — TYP-21 ratings backend
- `FRIENDSHIPS_ENDPOINTS.md` — TYP-22 friendships backend (includes the auto-accept-on-mutual-pending logic referenced in §5)
- `ML_RATING_UNDERSTANDING.md` — `derived_score`, `attributed_effect`, `events.weight` — the ML-side schema this design feeds into
- `JWT_AUTH_UNDERSTANDING.md` — auth pipeline reference
- `ALEMBIC_NOTES.md` — migration patterns (relevant for the bio-field migration)
- `handoff-05-02.md` — the strategic reframe that put iOS-with-friends on the critical path; the original timeline math

---

## Notes for Claude Code (with Linear MCP)

When filing tickets:

1. **Each ticket should reference this doc** in its description: "See `Design Handoff 2026-05-09 §X.Y` for full spec."
2. **Use the estimates in §6 as initial Linear estimates.** Round generously — these are floor-level estimates.
3. **Sort tickets into the existing TYP-* sequence** where possible. Backend tickets get small numbers (TYP-3X range), iOS feature tickets attach to existing TYP-27 through TYP-31 or get new numbers.
4. **Flag dependencies explicitly** in Linear's "blocked by" relationship field. Per-ticket dependencies are listed in §6's Dependencies column.
5. **DO NOT file v1.1 tickets in the same project as v1 tickets.** Either separate Linear project, or tag with `v1.1` label so they don't pollute v1 burn-down.
6. **The Open Questions in §7 are NOT tickets.** They're decisions Alan needs to make before some tickets can be implemented. Surface them to Alan, don't file them as tickets.
7. **Memory**: after filing tickets, update memory with the new ticket numbers and a one-line summary so future Claude sessions know what's been filed.