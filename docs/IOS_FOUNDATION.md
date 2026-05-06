# iOS Foundation (TYP-25)

What got built, why, and what the next iOS ticket needs to know. Companion to `handoff-05-02.md` (which framed the iOS-first pivot).

Date: 2026-05-05
Branch: `typ-25-project-scaffold-api-client`

---

## TYP-25 acceptance status

| # | Criterion | Status |
|---|---|---|
| 1 | Xcode project created, runs in simulator | done |
| 2 | APIClient with base URL, async request, JWT auto-attach | done |
| 3 | JWT stored in Keychain (not UserDefaults) | done — wrapper exists, no token persisted yet (login flow is TYP-26) |
| 4 | Codable models for User / Event / Outing / Place / Friend / FeedItem | done |
| 5 | Hello-world `/health` from button tap | done — verified end-to-end against deployed Render instance |

All five met. Ready to commit + PR.

---

## Files added

```
ios/TypeA/TypeA.xcodeproj/                    Xcode project, synchronized-folder mode (Xcode 16 default)
ios/TypeA/TypeA/TypeAApp.swift                @main entry — unchanged from template
ios/TypeA/TypeA/ContentView.swift             "Ping /health" button + status text + spinner
ios/TypeA/TypeA/APIClient.swift               singleton APIClient, generic request<T: Decodable>
ios/TypeA/TypeA/KeychainStore.swift           singleton Keychain wrapper (set / get / delete)
ios/TypeA/TypeA/Models.swift                  9 Decodable structs/enums mirroring backend Pydantic schemas
ios/TypeA/TypeA/Assets.xcassets/              app icon + accent color (template defaults + custom logo)
```

No SPM dependencies. No CocoaPods. No Tuist. Just the vanilla Apple toolchain.

---

## Locked design decisions

### Project setup
- **Storage: None.** No SwiftData, no CloudKit hosting. Postgres on Render is the source of truth — iOS is a thin client. SwiftData would be a local cache layer that would compete with the simple "fetch from API, render" pattern. Bolt it on later if/when offline mode is a real requirement.
- **Synchronized folders enabled** (Xcode 16 default). Files written into `ios/TypeA/TypeA/` (or subfolders) appear in the project navigator automatically — no `.pbxproj` editing or drag-into-Xcode step. This makes Claude-driven file writes work cleanly.
- **iOS 17 minimum** (Xcode default).
- **Bundle ID:** `app.alan.TypeA`. Product/module name: `TypeA` (PascalCase, no space, no hyphen — see `project_naming.md` memory).
- **No XCTest target.** Matches backend (no test framework yet).

### APIClient (`APIClient.swift`)
- **Singleton class** (`APIClient.shared`). Not an actor — `URLSession.shared.data(for:)` is already async-safe and the keychain access is sync-fast.
- **Generic `request<T: Decodable>(_:method:) async throws -> T`.** One method handles every endpoint. Call site supplies the type via type inference: `let user: User = try await APIClient.shared.request("/me")`.
- **Base URL** hardcoded to `https://type-a-api.onrender.com`. No `#if DEBUG` localhost switch yet — when needed, the right place is the `baseURL` property.
- **JSON decoder configured once** (private property): `dateDecodingStrategy = .iso8601`, `keyDecodingStrategy = .convertFromSnakeCase`. The latter auto-maps `user_id` → `userId` so models use idiomatic camelCase without per-field `CodingKeys`.
- **JWT auto-attach** is a 3-line conditional read from `KeychainStore.shared.get("auth_token")` and a `setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")` if non-nil. When the keychain is empty (pre-login), the header is skipped — that's why `/health` works today without a JWT.
- **Errors** thrown as `APIError(statusCode:body:)` for non-2xx, propagating Swift's normal `URLError` for transport failures.

### KeychainStore (`KeychainStore.swift`)
- **Hand-rolled wrapper** around `Security.framework`. ~50 lines. No SPM dependency on `KeychainAccess` or similar — the wrapper covers what the app needs, no more.
- **Service namespace:** `app.alan.TypeA` (matches bundle ID).
- **`set(_:for:)` is delete-then-add.** `SecItemAdd` errors if the item already exists; deleting first avoids needing to detect existence and call `SecItemUpdate` separately. Net effect: idempotent upsert.
- **`get(_:)` returns `String?`** — nil on `errSecItemNotFound` rather than throwing. Failure is the common case (pre-login), not exceptional.
- **`delete(_:)` is fire-and-forget.** Status not checked — if the item doesn't exist, `SecItemDelete` returns `errSecItemNotFound` and we don't care.
- **Why Keychain over UserDefaults:** UserDefaults is a plist in the app sandbox, readable in plaintext via filesystem access (jailbroken device, backup forensics). Keychain is encrypted at rest, hardware-backed on Secure Enclave devices, and isolated per-app.

### Models (`Models.swift`)
- **One file** for now. ~95 lines. Split into a `Models/` folder if it grows past a few hundred.
- **Naming:** `User`, `Place`, `Event`, `Outing`, `Friend`, `FeedItem` — dropped the `*Out` suffix from the Pydantic side. The backend's in/out distinction (`UserCreate` vs `UserOut`) doesn't apply on the frontend, so the suffix would just be noise. Cross-codebase the mapping is obvious (`UserOut` ↔ `User`).
- **camelCase fields** (e.g. `userId: UUID`, `displayName: String`) auto-mapped from JSON snake_case via the decoder strategy. No per-field CodingKeys needed.
- **`UUID` and `Date` directly** as field types — `JSONDecoder` decodes UUIDs from strings and ISO8601 dates from strings out-of-the-box once the strategies are set.
- **`FeedItem` is a discriminated enum** (`case rating(FeedRating)`, `case save(FeedSave)`, `case outing(FeedOuting)`) with a custom `init(from:)` that reads the `type` discriminator and dispatches to the right case-struct decoder. Mirrors the backend's `FeedRatingOut | FeedSaveOut | FeedOutingOut` tagged union. Same pattern as Rust's `#[serde(tag = "type")]` or TypeScript discriminated unions.
- **No `Identifiable` conformance yet.** Will add when SwiftUI `ForEach` lists need it; the `id` source per type is obvious (`User.userId`, `Place.placeId`, etc.).

---

## Gotchas worth knowing

- **Render free-tier cold starts:** first API call after ~15 min of idle wakes a sleeping container. Expect ~30–60 sec hang on first tap. Subsequent calls are ~250ms. iOS will *look* frozen but the spinner is genuine — don't add aggressive timeouts.
- **Simulator vs. physical device:** simulator works without iPhone Developer Mode. Use simulator for fast iteration, switch to device only when you need real Keychain / Camera / Push behavior.
- **Synchronized folders sometimes need a refresh.** If a newly-written file doesn't appear in Xcode's navigator, close + reopen the project (Cmd+Q, reopen). Don't hand-edit `.pbxproj`.
- **Bearer header is conditional.** If you write a new endpoint that requires auth and Keychain is empty, the request will go out without `Authorization` and the backend will 401. This is correct behavior — TYP-26 (login) is what makes this work end-to-end.

---

## What is NOT done (intentionally)

- **No login UI / Supabase client.** That's TYP-26. `KeychainStore.shared.set("...", for: "auth_token")` exists and works; nothing calls it yet.
- **No tab bar / app shell.** That's TYP-10 (SwiftUI skeleton, 4 tabs).
- **No real screens** — just the `/health` ping button. Place search, plan tab, friends, feed, ratings: all separate tickets.
- **No request body / encoder support.** `APIClient.request<T>` is GET-only as written. POST/PATCH support is one method addition (encode a `Body: Encodable` to JSON, set `httpBody` and `Content-Type`) — wait until the first ticket that needs it (probably TYP-26 for the Supabase login POST or some user-create flow).
- **No model writeback / Encodable models.** All models are `Decodable`-only. When POST/PATCH endpoints get wired up, the relevant types add `Encodable`.
- **No Identifiable, Hashable, Equatable conformances.** Add per type as the consuming SwiftUI code requires them.
- **No error UI affordance beyond raw `APIError` text in `ContentView`.** The current "200 OK — status: ok" / "HTTP 4xx: ..." / "Network error: ..." rendering is debug-grade. Every real screen will need its own error states.
- **No token refresh.** Supabase JWTs expire (default ~1 hour). When a request returns 401 because the access token is stale, the client should use the refresh token to get a new access token and retry the original request. Neither `APIClient` nor `KeychainStore` implements this yet. TYP-26 (or a small follow-up after it) needs to: (a) store both `access_token` and `refresh_token` in Keychain (separate keys), (b) add 401-handling inside `APIClient.request<T>` that calls Supabase's refresh endpoint, persists the new tokens, and retries once, (c) handle the refresh-also-failed case by deleting tokens and routing the user back to login. Without this, the user gets silently logged out the first time their token expires mid-session.

---

## Picking up the next iOS ticket

Per the iOS sequencing in `project_ios_first_sequencing.md` memory: **TYP-25 → TYP-10 → TYP-26 → 27 → 28 → 29 → 30 → 31**. So **TYP-10 (SwiftUI skeleton, 4 tabs)** is technically next — that's the tab-bar shell with placeholder views per tab. It doesn't depend on auth and unblocks all per-tab tickets. TYP-26 (auth) typically lands the user *into* the tab shell, so building the shell first makes sense.

Below is the concrete starter for TYP-26 since it's the higher-leverage one (auth unlocks every authenticated endpoint), but TYP-10 should ship first.

### TYP-26 (Auth flow — login + register)

Concrete first steps when you start TYP-26:

1. **Add Supabase client** — Supabase has an official Swift SDK (`supabase-swift`) on SPM. File → Add Package Dependencies → `https://github.com/supabase/supabase-swift`. Or hand-roll the password-grant POST against `<SUPABASE_URL>/auth/v1/token?grant_type=password` if you'd rather avoid the dependency.
2. **Build a `LoginView`** with email + password text fields and a sign-in button.
3. **On successful sign-in**, extract the `access_token` from the response and call `try KeychainStore.shared.set(token, for: "auth_token")`. After this, every `APIClient.shared.request(...)` call will auto-attach the Bearer header.
4. **Verify with `/me`** — pick a screen that calls `APIClient.shared.request("/me")` returning `User`. If the JWT round-trip is wired correctly, you'll see the authenticated user struct decoded.
5. **Add logout** — `KeychainStore.shared.delete("auth_token")`. Optionally route the user back to the login view.
6. **Decide where logged-in state lives.** Two common patterns: (a) an `@Observable` `AuthStore` singleton that exposes `var user: User?` and watches the keychain, (b) check `KeychainStore.shared.get("auth_token") != nil` directly at startup. (a) is cleaner for SwiftUI; (b) is fewer lines.

The data model is wired — every endpoint you'll hit in TYP-26 (`/me`, `/me/friends`, etc.) already has its Swift type ready in `Models.swift`.

---

## Code recipes

### Typed GET request
```swift
let user: User = try await APIClient.shared.request("/me")
let outings: [Outing] = try await APIClient.shared.request("/me/outings")
let feed: FeedResponse = try await APIClient.shared.request("/me/feed?limit=20")
```

### Persisting the JWT after login (TYP-26 will use this)
```swift
let token = supabaseSession.accessToken
try KeychainStore.shared.set(token, for: "auth_token")
// Every subsequent APIClient.shared.request(...) call now auto-attaches
// `Authorization: Bearer <token>`. No further changes to call sites.
```

### Logging out
```swift
KeychainStore.shared.delete("auth_token")
// Optionally route the user back to the login view
```

### Handling errors at a call site
```swift
do {
    let user: User = try await APIClient.shared.request("/me")
    // use user
} catch let error as APIError {
    // backend returned non-2xx; error.statusCode and error.body are available
} catch {
    // transport failure, timeout, JSON decode error
}
```

### Decoding a feed response (discriminated union)
```swift
let response: FeedResponse = try await APIClient.shared.request("/me/feed?limit=20")
for item in response.items {
    switch item {
    case .rating(let r): print("\(r.displayName) rated \(r.placeName) \(r.rating)")
    case .save(let s):   print("\(s.displayName) saved \(s.placeName)")
    case .outing(let o): print("\(o.displayName) finished \(o.title)")
    }
}
```

---

## References

- **Memory:** `project_ios_structure.md`, `project_ios_first_sequencing.md`, `project_naming.md`, `project_prediction_ux.md`
- **CLAUDE.md** — project-wide context, endpoint inventory, hooks, conventions
- **`handoff-05-02.md`** — the strategic pivot that put iOS on the critical path (predates TYP-24 deploy)
- **Backend Pydantic schemas** — source of truth for Swift model field names: `backend/app/schemas/*.py`
