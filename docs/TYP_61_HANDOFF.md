# TYP-61 + TYP-41 Handoff — Profile settings screen and bio field

**Status as of 2026-05-15:** Merged in PR #27 (commit `33fb8de`). Branch was `typ-61-ios-profile-settings-sheet`. Bundled two Linear tickets in one PR — TYP-41 (1pt backend `bio` field) and TYP-61 (4pt iOS settings screen).

---

## Why bundled

TYP-41 is the data dependency for TYP-61's bio row. Splitting them across two PRs would mean shipping an iOS screen that pretends bio exists, then patching it after the backend lands — pointless churn for what is in total a small change. One PR closes both tickets via `Fixes TYP-41` / `Fixes TYP-61`.

---

## What shipped

### Backend — `users.bio TEXT NULL`

- **Migration** `b416388ba296_add_bio_to_users.py` — `op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))` + matching `op.drop_column` downgrade. No backfill needed since column is nullable.
- **`models/users.py`** — `bio: Mapped[str | None] = mapped_column(Text)`. Column is unbounded `TEXT` — the length cap is a presentation/API concern, not a storage one.
- **`schemas/users.py`** — `UserOut` exposes `bio: str | None = None`. `UserUpdate` enforces a 160-char ceiling server-side via `Field(default=None, max_length=160)` — Pydantic returns 422 on oversized bios. Single source of truth for the cap.
- **`repositories/users.py`** — `update_user` accepts a `bio` kwarg, follows the existing `if x is not None` pattern.
- **`routes/users.py`** — `PATCH /me` passes `bio=body.bio` through.

### iOS — `SettingsView` + Profile rewiring

- **New file** `ios/TypeA/TypeA/Views/SettingsView.swift` — the actual screen.
- **`Models.swift`** — `User` gains `bio: String?`. `UserUpdate` gains `bio: String?`. The one existing call site (`AuthStore.signUp`) updated to pass `bio: nil` explicitly.
- **`MainTabView.swift:18`** — `ProfileView()` is now wrapped in `NavigationStack { ... }`. Only the Profile tab gets it for now; other tabs unchanged.
- **`ProfileView.swift:64`** — gear icon `Button` replaced with `NavigationLink { SettingsView() } label: { ... }`. The label is the existing gear styling verbatim.
- **`ProfileView.swift:85`** — `identityBlock` now renders `currentUser?.bio ?? "Tap settings to add bio"`. Real bio when set; italic placeholder when nil.
- **Orphan cleanup**: `logoutButton` view property + the `isSigningOut` state + the bottom-anchored `signOut()` method on `ProfileView` are gone — they all live in `SettingsView` now.

### Drive-by — `APIClient.swift` date decoding

A latent bug, surfaced this session. Postgres stores microsecond precision (`2026-04-30T23:25:29.523774-04:00`). Swift's `JSONDecoder.DateDecodingStrategy.iso8601` is strict — it rejects fractional seconds entirely. This had been silently failing anywhere a populated table returned dates (`/me`, `/me/place_ratings`, `/me/outings`, `/saved_places`).

Replaced with a `.custom` strategy that:
1. Truncates fractional seconds to 3 digits (millisecond precision) via regex
2. Tries `ISO8601DateFormatter` with `.withFractionalSeconds`
3. Falls back to plain `ISO8601DateFormatter` for seconds-only timestamps
4. Throws a clear `DecodingError` with the raw string if both fail

Applies to **every** decoded response, not just `/me`. Anything that fetches dates benefits.

---

## Design decisions worth knowing

### Push, not modal sheet

Ticket text says "presented modally from the gear icon." Settings is now a **`NavigationStack` push** instead.

Why diverged: settings is *hierarchical* — it's a sub-page of Profile, conceptually. Instagram, X, Threads, GitHub all push their settings screen. Sheets are for *temporary interruptions* (compose, share, ephemeral confirm). When you tap the gear, you're going *to* settings, not interrupting yourself. The push UX also keeps the tab bar visible, which is the convention.

Implementation cost: same. `NavigationLink` instead of `.sheet`.

### Row-style edit pattern, not inline `TextField`s

First pass used a `Form` with `TextField` rows for display name and bio — the obvious iOS Settings pattern. Alan rejected the look as too flat.

Final pattern (per Alan's suggestion):

```
┌── Edit Profile ──────────────────┐
│ Display Name      Alan       ✏️ │
│ Bio               Add a bio  ✏️ │
└──────────────────────────────────┘
```

- Bold label on the left
- Grayed current value (or placeholder) in the middle
- Pencil icon on the right
- Entire row is tappable

Tap → presents an **`EditFieldSheet`** with a single `TextField`, autofocused, with a `Cancel` (left) / `Done` (right) toolbar. Done writes the draft back to the parent's `@State`; Cancel discards. Bio variant has the 160-char clamp + `count / 160` caption.

### Two-stage save

Per-field edits mutate local `@State` only. The top-level **Save** button in `SettingsView`'s toolbar is what actually fires `PATCH /me`. Single network call regardless of how many fields you edited. Save is disabled until at least one field actually differs from `authStore.currentUser`.

On successful save, the response replaces `authStore.currentUser` directly — `ProfileView.identityBlock` re-renders immediately without a re-fetch.

### Bio clearing semantics

Repository pattern is `if bio is not None: user.bio = bio`. That means `None` from a client means "don't touch," not "clear to NULL." So clients can never wipe a bio back to NULL — but they *can* clear it to `""` by sending an empty string. The UI treats both null and empty as "no bio," so this is fine.

Send-side: `SettingsView` always sends `bio: bio.trimmingCharacters(in: .whitespacesAndNewlines)`, even if empty. That guarantees a clear-the-bio gesture in the UI maps to an empty string in storage. Display name uses the same trim but adds a `guard !trimmedName.isEmpty` — empty display name is a validation error, not a wipe.

### Logout in Settings, not on Profile

The temporary red Logout button at the bottom of Profile is now gone. Logout lives in the final section of `SettingsView` with a destructive-role button. Same `authStore.signOut()` flow, same `isSigningOut` ProgressView. The settings section dividers for **Notifications**, **Privacy**, and **Blocked users** are laid out as `.disabled(true)` "Coming soon" placeholders per the ticket — easy to fill in for v1.x without re-arranging the screen.

---

## Out of scope

- **Bio character cap UX on Profile**: the identity block doesn't truncate or `lineLimit` the bio yet. Long bios will just expand the row vertically. Fine for v1 with a 160-char cap.
- **Notifications / Privacy / Blocked users actual UI**: per ticket, only the section placeholders ship.
- **Profile photo upload**: TYP-55 (v1.1), still punted.

---

## Open follow-ups for the next session

- **TYP-49 — iOS Place detail screen** is the agreed next ticket. 8 pts, Medium priority. The detail screen is the hub when a place row is tapped from Search / Profile / Feed. No backend dependencies; the data shape comes from existing `/places/{id}/predict`, `/places/{id}/my_rating`, and place fields. Friends-who-rated/saved-this-place section may want a new backend endpoint — decide once at start.
- **Two-line cleanup in ProfileView** (cosmetic, optional): `isSigningOut` state at `ProfileView.swift:27` and `signOut()` func at `ProfileView.swift:491-495` are leftover after the orphan deletion — both are unused. Swift won't warn but they could be removed for tidiness.
- **`Local.xcconfig` IP staleness** surfaced during testing this session — the file's `API_BASE_URL` pointed at a stale LAN IP, but the Mac had rotated to a Tailscale-only interface. Either `localhost:8000` (simulator) or the current Tailscale IP (device, both peers on Tailnet) works. Not committed; per-dev concern.

---

## Files touched

Backend:
- `backend/alembic/versions/b416388ba296_add_bio_to_users.py` (new)
- `backend/app/models/users.py`
- `backend/app/schemas/users.py`
- `backend/app/repositories/users.py`
- `backend/app/routes/users.py`

iOS:
- `ios/TypeA/TypeA/Views/SettingsView.swift` (new)
- `ios/TypeA/TypeA/Views/ProfileView.swift`
- `ios/TypeA/TypeA/Views/MainTabView.swift`
- `ios/TypeA/TypeA/Models.swift`
- `ios/TypeA/TypeA/Auth/AuthStore.swift`
- `ios/TypeA/TypeA/APIClient.swift`

Docs:
- `docs/CURRENT_HANDOFF.md` (entry added)
- `docs/TYP_61_HANDOFF.md` (this file)
