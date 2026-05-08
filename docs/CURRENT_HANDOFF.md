# TypeA — Current Handoff

Living doc. Updated as decisions are made, scope shifts, or tickets merge. For deeper per-ticket archaeology see `TYP_XX_HANDOFF.md` files; for evergreen architectural reference see the per-topic docs in this folder.

---

## Recent decisions

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
- **Implementation deferred** until iOS ships real rating data. Recommendations endpoint will use popularity-fallback in v1.

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