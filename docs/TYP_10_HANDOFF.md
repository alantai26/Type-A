# TYP-10 Handoff — 4-Tab Navigation Shell

**Merged:** 2026-05-08
**Branch:** TYP-10-tab-shell
**Predecessors:** TYP-25 (Xcode + APIClient), TYP-26 (auth flow)
**Successors:** iOS Feed tab, iOS Plan tab, iOS Search tab, iOS Profile tab root (per-tab content tickets)

---

## What this ticket shipped

A 4-tab `TabView` (Feed / Plan / Search / Profile) wired into `RootView` for authenticated users. Profile tab inherits TYP-26's greeting + email + logout content. Feed / Plan / Search render "Coming soon" empty-state placeholders styled per the design system. This PR is intentionally chrome-only — content lives in follow-up tickets.

---

## What I learned (SwiftUI mechanics walkthrough)

### TabView is just a container

SwiftUI is **declarative**, so unlike UIKit's `UITabBarController` (with delegates and view-controller arrays), all you do is nest views inside `TabView` and attach a `.tabItem` modifier:

```swift
TabView {
    FeedView()
        .tabItem { Label("Feed", systemImage: "newspaper") }
    PlanView()
        .tabItem { Label("Plan", systemImage: "calendar") }
    // ...
}
```

The bottom bar is rendered automatically. The order of children == the order of tabs left to right.

### `.tabItem` is metadata, not navigation

`.tabItem` is a view modifier that **attaches metadata** (a Label = title + icon) to each child. TabView reads that metadata to build the bottom bar. The modifier doesn't go inside the child view — it's applied where the child is placed *inside* TabView.

This is also why tapping a tab isn't a "navigation event" in the traditional sense — there's no push, no transition. SwiftUI just toggles which child is currently rendered.

### Each tab gets its own NavigationStack

You'll notice every tab view (FeedView, PlanView, SearchView, ProfileView) wraps its content in `NavigationStack`. That's intentional — each tab has its own **independent navigation history**.

Why this matters: from Profile, push the Friends sub-screen → tap to Feed → tap back to Profile. You'd want to land back on the Friends sub-screen, not at the Profile root. That works because each tab has its own stack.

If you put one `NavigationStack` *outside* the TabView wrapping everything, all tabs would share a single stack. Pushing a sub-screen in one tab would "leak" across tabs. Bad UX. So the canonical pattern is: **`TabView` outermost, `NavigationStack` inside each tab**.

### Tab view lifecycle: instantiated once, kept alive

When `MainTabView` first renders, **all 4 tab structs are instantiated up front**. SwiftUI keeps them alive in memory. Tapping a tab just toggles which one is visible — it doesn't create a new instance.

That matters for state. Scroll halfway down Feed → switch to Plan → come back to Feed → still scrolled halfway. The view instance never went away. Same with `@State` variables, search text, loaded data, everything.

This is also why `.task { ... }` (data loading) typically only runs once per view lifetime, not every tab switch — handy because you don't want to re-fetch the feed every tap.

### The render chain

```
TypeAApp (entry point, @main)
  └── RootView          ← decides: loading? login? main app?
        └── MainTabView ← when authenticated
              └── TabView
                    ├── FeedView
                    ├── PlanView
                    ├── SearchView
                    └── ProfileView (greeting + email + logout)
```

`RootView` reads `authStore.isAuthenticated` and conditionally renders `LoginView` OR `MainTabView`. `MainTabView` then composes the 4 tabs. Single source of truth: the auth state.

### Lifting MainView → ProfileView

`MainView.swift` was a placeholder built in TYP-26 to prove auth worked. In TYP-10, its body was lifted **verbatim** into a new `ProfileView`, and the original was deleted.

Lesson: when a view is scaffolding for a temporary state, design it so its body can be relocated when the real architecture lands. Keep the view stateless or rely on `@Environment` (as MainView did with `AuthStore`) so it can be moved without rewiring.

### Placeholder pattern (design system reuse)

Feed / Plan / Search render the same skeleton:

```swift
NavigationStack {
    VStack(spacing: 16) {
        Spacer()
        Image(systemName: "<sf-symbol>")
            .font(.system(size: 32, weight: .medium))
            .foregroundStyle(Color.accentColor)
            .frame(width: 72, height: 72)
            .background(Color.accentColor.opacity(0.12))
            .clipShape(Circle())
        VStack(spacing: 6) {
            Text("Coming soon")
                .font(.system(size: 24, weight: .bold, design: .rounded))
            Text("<conversational microcopy>")
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        Spacer()
    }
    .padding(.horizontal, 24)
    .navigationTitle("<Tab Name>")
}
```

This is the design system's empty-state pattern — orange icon-in-circle + rounded hero title + secondary subtitle + 24pt page padding. Reuse it for any future "no content yet" surfaces.

---

## Files touched

**Added:**
- `ios/TypeA/TypeA/Views/MainTabView.swift` — 4-tab `TabView` composition
- `ios/TypeA/TypeA/Views/FeedView.swift` — placeholder
- `ios/TypeA/TypeA/Views/PlanView.swift` — placeholder
- `ios/TypeA/TypeA/Views/SearchView.swift` — placeholder
- `ios/TypeA/TypeA/Views/ProfileView.swift` — lifted from MainView (greeting + email + logout)

**Modified:**
- `ios/TypeA/TypeA/Views/RootView.swift` — renders `MainTabView()` instead of `MainView()` when authenticated

**Deleted:**
- `ios/TypeA/TypeA/Views/MainView.swift` — body lifted into ProfileView

**Tab icons (SF Symbols):**
- Feed: `newspaper`
- Plan: `calendar`
- Search: `magnifyingglass`
- Profile: `person.circle`

---

## What's next

The 4 placeholder tabs are scaffolding for follow-up tickets that fill in real content:

- **iOS - Feed tab** → Trending rail + friend activity timeline (see Feed mockup in CURRENT_HANDOFF.md 05-07-later)
- **iOS - Plan tab** → segmented `Plans | History` + creation modal (event vs outing flip on stop count)
- **iOS - Search tab** → place search + "Recommended for you" rail
- **iOS - Profile tab root** → expanded profile with sub-screen nav rows (Friends, Activity, Settings)

All four depend on TYP-10 landing first; that's now done.
