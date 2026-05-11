# Tab Switching — Understanding

Plain-language explanation of how tab switching works in TypeA. Use this when you forget *why* you wrote the code the way you did. Companion to `TYP_38_HANDOFF.md`.

The same pattern is reused for any shared state in the app (current user, feed cursor, friends list, etc.). Tabs are just the simplest concrete example.

---

## The problem

When you tap **"Find places to rate"** on the empty Profile screen, you want the app to jump to the Search tab.

But `ProfileView` and `MainTabView` (the thing that owns the tab bar) are different views in different files. A child view can't directly reach up and command its parent — they need some *shared piece of state* both of them can see.

That's the whole problem in one sentence. Everything we built is a way to give them a shared piece of state.

---

## The mental model

Picture the app as a tree:

```
TypeAApp
  └─ RootView
       └─ MainTabView                ← decides which tab shows
            ├─ FeedView
            ├─ PlanView
            ├─ SearchView
            └─ ProfileView           ← wants to say "go to Search!"
```

Solution: put a small object high up in the tree (above MainTabView), then have everyone below it agree to read/write to it. When `ProfileView` changes the value, `MainTabView` sees the change and switches tabs.

That object is `TabSelectionStore`. It holds exactly one thing: which tab is active.

---

## The stadium scoreboard analogy

Picture a baseball stadium.

- **The scoreboard hangs above the field** — everyone in the stadium can see it. That's `TabSelectionStore`.
- **It currently shows "FEED"**. That's `tabSelection.current`.
- **The stadium owner bolted the scoreboard to the wall** before the game started and said "this is *the* scoreboard, everyone refer to it." That's `TypeAApp` doing `.environment(tabSelection)`.

Three actors in the stadium:

- **The announcer up in the booth** keeps one eye on the scoreboard. Whatever it says, they show that team's footage on the big-screen TV. → That's `MainTabView` showing whichever tab matches `current`.
- **A coach on the field** can walk up to the scoreboard and change the value. → That's `ProfileView` running `tabSelection.current = .search` when you tap the CTA.
- **The fans** can also walk up and change it. → That's the user tapping the bottom tab bar.

**The magic ingredient: the scoreboard has a bell on top.** Whenever anyone writes a new value, the bell rings. The announcer hears it, glances at the new value, and switches the big-screen TV to match.

The `@Observable` keyword on `TabSelectionStore` is what installs the bell. Without it, the scoreboard would still exist and people could still change it — but the announcer wouldn't know it changed, and the screen would never switch. **`@Observable` is the bell.**

---

## The full trace when you tap "Find places to rate"

1. User taps the orange pill in `ProfileView`'s empty-state card
2. `Button` action fires: `tabSelection.current = .search`
3. The `@Observable` system sees the property changed → 🔔 notifies all watchers
4. `MainTabView`'s `body` re-evaluates because it watches `tabSelection.current`
5. `TabView(selection: $tabSelection.current)` now has `selection == .search`
6. SwiftUI looks for the child with `.tag(AppTab.search)` and displays it
7. SearchView appears, bottom tab bar's "Search" icon highlights

All of that happens in roughly one frame, so it just looks like "tap → switch."

---

## The four files, mapped to the analogy

| Stadium thing | Code |
|---|---|
| The scoreboard exists | `TabSelectionStore.swift` defines the class |
| The bell on top | `@Observable` on the class |
| Owner bolts it to the wall | `TypeAApp.swift` injects it with `.environment(tabSelection)` |
| Announcer watching it | `MainTabView.swift` reads it via `@Environment(...)` |
| Coach changing the score | `ProfileView.swift` writes `tabSelection.current = .search` |

### File 1 — `TabSelectionStore.swift` (the scoreboard)

```swift
enum AppTab: Hashable {
    case feed, plan, search, profile
}

@MainActor
@Observable
final class TabSelectionStore {
    var current: AppTab = .feed
}
```

- `AppTab` is an enum — a fixed list of 4 values. Using an enum (instead of a string like `"feed"`) means the compiler catches typos.
- `@Observable` is Apple's marker for "when any `var` on this class changes, anyone watching re-renders."
- `current` starts at `.feed` — so when the app launches, the Feed tab shows first.

### File 2 — `TypeAApp.swift` (bolting it to the wall)

```swift
@State private var authStore = AuthStore()
@State private var tabSelection = TabSelectionStore()

var body: some Scene {
    WindowGroup {
        RootView()
            .environment(authStore)
            .environment(tabSelection)
    }
}
```

`.environment(tabSelection)` says "this object is now available to every view under `RootView`." Same way `AuthStore` is reachable everywhere.

### File 3 — `MainTabView.swift` (the announcer)

```swift
@Environment(TabSelectionStore.self) private var tabSelection

var body: some View {
    @Bindable var tabSelection = tabSelection
    TabView(selection: $tabSelection.current) {
        FeedView()
            .tabItem { Label("Feed", systemImage: "newspaper") }
            .tag(AppTab.feed)
        // ...etc for the other 3 tabs
    }
}
```

Three new things:

1. `@Environment(...)` reads the store we injected in `TypeAApp`.
2. `@Bindable var tabSelection = tabSelection` is the magic line. `@Observable` objects don't give you bindings directly; `@Bindable` wraps it so you can write `$tabSelection.current` to get a two-way connection to the value. The shadowing (`var x = x`) looks weird but is Apple's documented pattern.
3. `.tag(AppTab.feed)` etc. tells SwiftUI: "the tag for this child is `.feed`." Now when `tabSelection.current == .feed`, SwiftUI shows that child.

The binding goes both directions: when the user taps the tab bar at the bottom, SwiftUI writes back into `tabSelection.current`. When code changes `tabSelection.current`, the displayed tab changes. Same plumbing, both directions.

### File 4 — `ProfileView.swift` (the coach changing the score)

```swift
@Environment(TabSelectionStore.self) private var tabSelection

// inside the CTA Button:
Button {
    tabSelection.current = spec.targetTab
} label: {
    Text(spec.ctaLabel) ...
}
```

When the user taps "Find places to rate":

- `spec` is the empty-state spec for the Places tab, which now has `targetTab: .search`
- The button action runs `tabSelection.current = .search`
- Because `tabSelection` is `@Observable`, SwiftUI knows the value changed → rings the bell
- `MainTabView`, watching that same value, sees the change and shows SearchView

The full per-tab mapping in ProfileView:

| Empty state | targetTab |
|---|---|
| Places | `.search` |
| Outings | `.plan` |
| Saved | `.search` |

---

## Why this pattern matters beyond tabs

Any view, anywhere in the app, can now switch tabs by writing to `tabSelection.current`. The same Observable + Environment pattern shows up everywhere:

- **`AuthStore`** — already in the app. Same shape: `@Observable` class, injected once in `TypeAApp`, read by any view that needs `currentUser`.
- **Future: a `FeedStore`** for cursor pagination on the Feed tab.
- **Future: a `FriendsStore`** to cache the friends list across screens.
- **Future: a `RankingSessionStore`** to hold the in-flight comparison loop state.

Build the infrastructure once, use it everywhere. That's what makes it worth doing now even for "just one button."

---

## Common gotchas

- **`@Bindable` shadowing** — you must write `@Bindable var tabSelection = tabSelection` inside `body`. If you try `$tabSelection.current` without the `@Bindable` line, Swift will reject it.
- **`.tag()` types must match** — `TabView(selection: $tabSelection.current)` is typed as `AppTab`, so each `.tag(...)` must also be an `AppTab`. Tagging with a `String` or `Int` won't work.
- **SourceKit lag on new files** — when you add a new `@Observable` class file, Xcode often shows red squiggles on every file that references it ("Cannot find 'X' in scope") until you Clean Build (Cmd+Shift+K → Cmd+B). The code compiles fine; SourceKit is just slow to re-index.
- **Don't mutate the store off the main thread** — `@MainActor` on the class enforces this. SwiftUI updates must happen on the main thread or the UI breaks in subtle ways.
