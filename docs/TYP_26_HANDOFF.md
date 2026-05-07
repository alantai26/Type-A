# iOS Auth Flow (TYP-26)

What got built, why, and what the next iOS ticket needs to know. Builds on `TYP_25_HANDOFF.md` (TYP-25).

Date: 2026-05-06
Branch: `typ-26-ios-auth-flow-login-register`

---

## TYP-26 acceptance status

| # | Criterion | Status |
|---|---|---|
| 1 | Login screen → Supabase sign-in → JWT stored | done — verified end-to-end against deployed Render `/me` |
| 2 | Register screen → Supabase sign-up → JWT stored | done; also writes `display_name` via `PATCH /me` |
| 3 | App launch checks JWT validity, routes to login or main | done — `RootView` switches on `AuthStore.isAuthenticated` + `!session.isExpired` |
| 4 | Logout clears JWT and routes to login | done — Supabase SDK clears its session, auth state listener flips `isAuthenticated` |
| 5 | Error states (wrong password, network fail) handled in UI | done — `LoginView` and `SignupView` show `error.localizedDescription` inline |

All five met.

---

## Files added / modified

```
ios/TypeA/Local.xcconfig                              gitignored — real SUPABASE_URL, key, API_BASE_URL
ios/TypeA/Local.example.xcconfig                      committed template
ios/TypeA/TypeA/Info.plist                            three custom keys read from xcconfig vars
ios/TypeA/TypeA/AppConfig.swift                       Bundle.infoDictionary reads, fatalError on missing
ios/TypeA/TypeA/Auth/AuthService.swift                Supabase SDK wrapper — signIn/signUp/signOut + currentAccessToken
ios/TypeA/TypeA/Auth/AuthStore.swift                  @MainActor @Observable state — subscribes to authStateChanges, loads /me
ios/TypeA/TypeA/Views/RootView.swift                  router — Login or Main on auth state
ios/TypeA/TypeA/Views/LoginView.swift                 email + password + sheet button to Signup
ios/TypeA/TypeA/Views/SignupView.swift                display_name + email + password + cancel
ios/TypeA/TypeA/Views/MainView.swift                  greeting + logout — placeholder for TYP-10 tab shell
ios/TypeA/TypeA/APIClient.swift                       modified — token from AuthService; new request<T, Body> overload for PATCH/POST
ios/TypeA/TypeA/Models.swift                          modified — added UserUpdate Encodable
ios/TypeA/TypeA/TypeAApp.swift                        modified — render RootView, inject AuthStore via @State + .environment
ios/TypeA/TypeA/Assets.xcassets/AccentColor.colorset  filled with FF9F1C orange
ios/TypeA/TypeA/ContentView.swift                     deleted (RootView replaces it)
.gitignore                                            modified — adds ios/TypeA/Local.xcconfig
```

Plus Xcode UI configuration (lives in `project.pbxproj`):
- Project-level Configurations set to `Local.xcconfig` for Debug + Release
- Custom iOS Target Properties: `SupabaseURL`, `SupabasePublishableKey`, `APIBaseURL` referencing `$(...)` build settings
- Supabase SPM dependency added + linked to TypeA target's "Frameworks, Libraries, and Embedded Content"

---

## Locked design decisions

### Auth architecture: SDK is source of truth

- **Supabase SDK manages the session.** It stores tokens in iOS Keychain internally (under its own service namespace), refreshes them transparently, and emits `authStateChanges` events.
- **`AuthService` is a thin wrapper** — singleton `final class`, exposes `signIn / signUp / signOut / currentAccessToken()`. The async `currentAccessToken()` calls `client.auth.session` which refreshes if needed.
- **`AuthStore` (`@MainActor @Observable`) tracks app-level state**: `isAuthenticated`, `currentUser`, `isInitializing`. It subscribes to `authStateChanges` once in `init()` and updates these properties when the SDK fires `signedIn`/`signedOut`/`tokenRefreshed`. Initial bootstrap checks `currentSession != nil && !isExpired`.
- **`APIClient` reads the access token via `AuthService.shared.currentAccessToken()`** before each request. Bearer header attached only when a token exists; `/health` still works pre-login because the header is conditional.
- **No custom Keychain wiring for the JWT.** `KeychainStore` (from TYP-25) still exists but isn't consumed for auth — the SDK's internal storage is enough. `KeychainStore` is reserved for future non-auth secrets (none yet).

### Token refresh: free via SDK

The SDK refreshes access tokens automatically when `currentSession` is accessed or when `for await ... in authStateChanges` yields a `tokenRefreshed` event. `APIClient` calls `await AuthService.shared.currentAccessToken()` per request, so we always have the freshest token. No manual 401-retry-with-refresh loop needed.

The Supabase 2.46 SDK prints a deprecation warning about `emitLocalSessionAsInitialSession` — we opted in via `SupabaseClientOptions(auth: .init(emitLocalSessionAsInitialSession: true))`, and `AuthStore.init` now also checks `!session.isExpired` to avoid bootstrapping with a stale token.

### Display name flow

Backend's `users.display_name` is set via `PATCH /me` (TYP-17 endpoint). After `AuthService.signUp(email:password:)` returns, `AuthStore.signUp` immediately calls `APIClient.shared.request("/me", method: "PATCH", body: UserUpdate(displayName: name))` and stores the returned User in `currentUser`.

The Supabase auth user (in Supabase's `auth.users`) only stores email + password hash. The TypeA user (in our Postgres `users`) stores display_name. They're different tables; the SDK doesn't know about `display_name`.

### APIClient PATCH/POST support

Added a `request<T: Decodable, Body: Encodable>(_:method:body:)` overload alongside the existing GET-only `request<T: Decodable>`. Internally both call a private `send<T, Body>` that handles optional body encoding. JSON encoder uses `keyEncodingStrategy = .convertToSnakeCase` to match the decoder's snake-to-camel handling — `UserUpdate(displayName: "Alan")` serializes as `{"display_name":"Alan"}`.

### Env config: xcconfig + Info.plist + Bundle reads

- `Local.xcconfig` (gitignored) holds real `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `API_BASE_URL`
- Wired at the project Configurations level (Debug + Release both use `Local`)
- Info.plist exposes them via `$(SUPABASE_URL)` build-setting references
- `AppConfig` reads via `Bundle.main.object(forInfoDictionaryKey:)`, `fatalError`s if missing — bad config crashes early, no silent fallbacks
- xcconfig parser quirk: URLs need `https:/$()/example.com` because `//` starts a comment in xcconfig syntax

### UI design system locked

See `project_design_system.md` memory. Summary: `FF9F1C` orange accent, iOS system colors for everything else, rounded-design hero type, 24pt page padding, 12pt corner radius on inputs and buttons, conversational microcopy. The accent flows through `Assets.xcassets/AccentColor.colorset`.

---

## Gotchas worth knowing

- **SPM is a two-step setup**: adding the package to the project ≠ linking the product to the target. After `File → Add Package Dependencies`, also go to `TARGETS → TypeA → General → Frameworks, Libraries, and Embedded Content → +` and add the `Supabase` product. Otherwise `import Supabase` fails with "No such module 'Supabase'."
- **`@MainActor` + `deinit`**: Swift 6 strict concurrency forbids `deinit` from accessing main-actor-isolated properties. We dropped the `deinit` from `AuthStore` entirely — the `[weak self]` in the auth-state-changes Task self-cleans when the store is deallocated. Don't add `deinit` back.
- **Supabase deprecation warning**: even after opting into `emitLocalSessionAsInitialSession: true`, the SDK still prints the deprecation note at AuthClient init. Informational, ignorable, will go away in the next major SDK version.
- **xcconfig URL escape**: `https://example.com` becomes `https:` (everything after `//` is a comment). Use `https:/$()/example.com`.
- **Synchronized folders are scoped to `TypeA/TypeA/`**: files at `ios/TypeA/Local.xcconfig` (sibling to `.xcodeproj`) won't auto-appear in Xcode. Use `File → Add Files to "TypeA"...` and **uncheck** "Add to target" (xcconfig isn't source).
- **`protect-files.sh` hook blocks `secrets`-named paths.** That's why we use `Local.xcconfig`, not `Secrets.xcconfig`. Don't try to rename — the hook regex includes `secrets` case-insensitive.

---

## What is NOT done (intentionally)

- **No tab bar / app shell.** That's TYP-10. `MainView` is a placeholder showing greeting + logout; the next ticket replaces it with a `TabView` and routes `/me` data to a Profile tab.
- **No real screens beyond auth + placeholder MainView.** Place search, plan, friends, feed, ratings, invitations — all per-tab tickets (TYP-27 through TYP-30).
- **No password reset / forgot password flow.**
- **No email verification UI.** Currently we set "Auto Confirm User" in Supabase dashboard so signup → immediately logged in. Production would need a verify-email screen.
- **No biometric unlock (Face ID).**
- **No OAuth (Google, Apple).** App Store requires Sign in with Apple if Google is offered, doubling the OAuth wiring. Punted for now; email/password is sufficient for TestFlight/alpha cohort.
- **No magic links (TYP-32 if ever).**
- **No retry-on-401 inside APIClient.** SDK refresh handles staleness, but if a refresh genuinely fails (refresh token revoked), the user gets logged out implicitly via the next `signedOut` state-change event. Could add explicit "refresh failed → bounce to login with toast" UX later.

---

## Picking up the next iOS ticket

Per `project_ios_first_sequencing.md`: **TYP-25 → 26 → 10 → 27 → 28 → 29 → 30 → 31**. So **TYP-10 (SwiftUI skeleton, 4 tabs)** is next.

### TYP-10 scope, recalibrated

The original TYP-10 ticket included "Profile tab shows current user from /me + logout button" as an acceptance criterion. **That's already done** in `MainView`. So the remaining TYP-10 scope is:

1. Replace `MainView`'s current single-screen layout with a `TabView`
2. Wire 4 tabs with SF Symbols icons + placeholder views
3. Each tab gets a `NavigationStack` for future push navigation
4. Move the existing greeting + logout into a "Profile" tab
5. Other 3 tabs show "Coming soon" placeholder

Suggested 4 tabs based on existing tickets: **Plan** (events/outings — TYP-19) / **Friends** (TYP-28) / **Activity** (TYP-30, your own log) / **Profile** (TYP-10). Worth confirming with Alan before wiring.

### How to wire it cleanly

- Add a new view `ProfileView` (move `MainView`'s body there)
- Add `RootTabView` — `TabView { PlanView() / FriendsView() / ActivityView() / ProfileView() }` each wrapped in `NavigationStack`
- Update `RootView` to render `RootTabView()` instead of `MainView()` when authenticated
- Each placeholder tab is ~10 lines (`Text("Coming soon").foregroundStyle(.secondary)`)
- Apply the design system consistently: navigation titles use rounded, system colors for everything

### Open question for Alan before TYP-10

Are the 4 tab labels above correct, or do you want different ones (e.g., "Feed" instead of "Activity")?

---

## Code recipes

### Authenticated GET request
```swift
let user: User = try await APIClient.shared.request("/me")
let outings: [Outing] = try await APIClient.shared.request("/me/outings")
```

### Authenticated PATCH/POST with body
```swift
let body = UserUpdate(displayName: "Alan Tai")
let updated: User = try await APIClient.shared.request("/me", method: "PATCH", body: body)
```

### Reading auth state in a SwiftUI view
```swift
struct SomeView: View {
    @Environment(AuthStore.self) private var authStore

    var body: some View {
        if let user = authStore.currentUser {
            Text("Hi, \(user.displayName)")
        }
    }
}
```

### Triggering signup from a view
```swift
try await authStore.signUp(email: email, password: password, displayName: displayName)
// On success, the SDK fires authStateChange → AuthStore flips isAuthenticated
// → RootView re-renders MainView automatically. No manual navigation.
```

### Triggering logout
```swift
try await authStore.signOut()
// SDK fires signedOut → AuthStore.isAuthenticated = false → RootView shows LoginView
```

### Reading an Info.plist-backed config value
```swift
// Inside AppConfig.swift — done already, no need to repeat at call sites.
// Just use AppConfig.supabaseURL, .supabasePublishableKey, .apiBaseURL.
```

---

## References

- **Memory:** `project_ios_structure.md`, `project_ios_first_sequencing.md`, `project_design_system.md`, `project_naming.md`, `project_prediction_ux.md`
- **CLAUDE.md** — endpoint inventory, hooks, conventions
- **`TYP_25_HANDOFF.md`** — TYP-25 handoff (project scaffold, APIClient, KeychainStore, Models)
- **Backend `app/auth.py`** — JWT validation logic; `/me` auto-provisions user on first hit
- **Backend `app/schemas/users.py`** — source of truth for `User` and `UserUpdate` shapes
- **Supabase Swift SDK 2.46** — `https://github.com/supabase/supabase-swift`
