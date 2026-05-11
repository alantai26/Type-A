# TYP-38 Handoff — iOS Profile Tab (own profile)

Per-ticket handoff for Linear TYP-38. Spec lives in `docs/05-09_HANDOFF.md §5`. Session started 2026-05-11.

## Status

| Slice | State |
|---|---|
| Empty-Places state | ✅ done |
| Empty-Outings state | ✅ done |
| Empty-Saved state | ✅ done |
| Tab strip switching | ✅ done |
| Identity block (avatar + name + bio placeholder) | ✅ done |
| Friends row card (zero-state) | ✅ done |
| Gear icon (visual only, no action) | ✅ done |
| CTA pills route to other tabs | ❌ blocked on `MainTabView` selection binding |
| Settings sheet (Edit profile + Logout move) | ❌ separate follow-up ticket |
| Populated Places list (ranked, Beli-style) | ❌ next slice |
| Populated Outings list | ❌ next slice |
| Populated Saved list | ❌ next slice |
| Friends row with real count + mutual avatars | ❌ next slice (needs TYP-43) |
| Header scroll-vs-pin decision | ❌ deferred until populated state exists |

## File map

Single file: `ios/TypeA/TypeA/Views/ProfileView.swift`.

Composition (top → bottom in the rendered screen):

```
ScrollView
  VStack(spacing: 0)
    headerRow          ← gear icon top-right, gray bubble
    identityBlock      ← 60pt orange initials avatar + name + bio placeholder
    friendsRow         ← gray card: person icon + "0 friends" + chevron
    tabStrip           ← Places | Outings | Saved, equal-width, orange underline on active
    emptyStateCard     ← icon-in-circle + title + subtext + orange CTA pill
    Spacer(minLength: 24)
    logoutButton       ← TEMPORARY — moves to gear sheet later
  .padding(.horizontal, 24)
```

Each section is a `private var name: some View` (or `private func` when parameters needed). The `body` reads top-to-bottom like a screen outline.

## State

```swift
@Environment(AuthStore.self) private var authStore  // app-wide, set in TypeAApp
@State private var selectedTab: ProfileTab = .places
@State private var isSigningOut = false
```

`ProfileTab` is a `private enum { .places, .outings, .saved }` with a `title` computed property. `EmptyStateSpec` is a `private struct` holding icon name + title + subtext + CTA label per tab. `emptyStateSpec(for:)` is a pure switch.

## Design system anchors used

- Orange accent: `Color.accentColor` (from the asset catalog `AccentColor` — same convention as `LoginView`/`SearchView`/etc.)
- Page padding: 24pt horizontal
- Card corner radius: 12pt
- Avatar fill: `Color.accentColor`, white text at 42% of circle diameter
- System grays via `Color(uiColor: .secondarySystemBackground)` / `.tertiarySystemBackground` / `.separator` — leading-dot syntax is ambiguous in newer SwiftUI SDKs because `SeparatorShapeStyle` collides; use `Color(uiColor:)` to be explicit
- Italic gray bio placeholder ("Tap settings to add a bio")

## Empty-state copy (locked 2026-05-11)

| Tab | Icon | Title | Subtext | CTA | Routes to |
|---|---|---|---|---|---|
| Places | `star` | No places yet | Click Search and rate your first place! | Find places to rate | Search tab |
| Outings | `calendar` | No outings yet | Plan your first outing and rate it! | Plan an outing | Plan tab |
| Saved | `bookmark` | Nothing saved yet | Search and save a place you want to go! | Find places | Search tab |

Pattern: 56pt orange-tinted icon circle (`Color.accentColor.opacity(0.15)` fill + `Color.accentColor` icon) → 16pt rounded-bold title → 14pt gray subtext (multiline, centered) → orange `Capsule` CTA pill.

## Known stubs (intentional)

| Stub | Why | Fix path |
|---|---|---|
| Gear icon button does nothing | Settings sheet is a separate follow-up ticket | New ticket for "Profile settings sheet" (Edit profile, Logout, future v1.x slots). Includes moving Logout out of ProfileView. |
| CTA pills don't switch tabs | `MainTabView` uses `TabView { ... }` without selection state. Children can't currently mutate the active tab. | (1) Add `@State private var selectedTab` to `MainTabView`; switch to `TabView(selection: $selectedTab)` with explicit `.tag(...)` per tab. (2) Inject the binding (or a tiny `@Observable TabSelectionStore`) into the environment. (3) Replace the empty-comment `Button` actions in `emptyStateCard` to mutate the binding. ~10–20 min. |
| `0 friends` is hard-coded | Friends count endpoint (TYP-43) not yet built, and friends data isn't on `User` | When TYP-43 ships, hydrate from `GET /users/{me}` response and render the overlapping mini-avatars from the first 3 friends. |
| Logout button visible at bottom of Profile | Settings sheet doesn't exist yet | Delete from `ProfileView` when the settings sheet ticket lands. |

## Known SourceKit noise

Xcode currently shows red squiggles on:
- `@Environment(AuthStore.self) private var authStore` → "Cannot find 'AuthStore' in scope"
- `Color(uiColor: .secondarySystemBackground)` and siblings → "No exact matches in call to initializer"

The code **compiles and runs** — these are SourceKit indexing failures, not real type errors. They clear on Cmd+Shift+K (Clean Build Folder) → Cmd+B. If they persist after that, check that `Auth/AuthStore.swift` is still in the target's compile sources.

## Next slice — recommended sequence

1. **Wire CTA pills to tab switching** (~10–20 min). Smallest follow-up. Makes the empty states feel "real."
2. **Populated Places list** — load `GET /me/place_ratings` (TYP-21 exists), render ranked rows per `docs/05-09_HANDOFF.md §5`. Visual: rank number + 32pt photo placeholder + name + category + orange rounded-bold score.
3. **Populated Outings list** — load `GET /me/outings` (TYP-19 exists), render completed outings only.
4. **Populated Saved list** — load `GET /me/saved_places` (TYP-18 exists, may need `q` optional per TYP-47).
5. **Real friends count** — depends on TYP-43 shipping.
6. **Settings sheet** — separate ticket; deletes the temporary Logout from ProfileView.

After all the above, header scroll-vs-pin becomes a real question. Default to "scrolls with the list" unless that feels wrong in practice.

## Out of scope for TYP-38 (do NOT pull in)

- Friend-view profile (TYP-50 covers it — same screen with auth-scoped variants)
- Place detail screen (TYP-49 — what you get when you tap a Places row)
- Friends sub-screen (TYP-28 — what you get when you tap the friends card row)
- Avatar photo upload (v1.1, TYP-55)
