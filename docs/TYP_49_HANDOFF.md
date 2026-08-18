# TYP-49 Handoff — iOS PlaceDetailView (functional v1)

Merged 2026-05-22 in PR #29 (commit `de0088d`). Branch was `typ-49-ios-place-detail-screen`. Bundled with TYP-65 backend (which shipped first in PR #28) and a drive-by TYP-21 fix.

Visual polish was deliberately deferred to TYP-67 — this PR ships the screen functionally complete but visually rough.

---

## What shipped

A new `PlaceDetailView` (`ios/TypeA/TypeA/Views/PlaceDetailView.swift`) reachable by tapping any place row in Profile's Places + Saved tabs. Four sections, top to bottom:

1. **Header** — category icon (60pt tinted circle, SF Symbol from `iconName(for:)` duplicated locally), name (32pt rounded bold), category (callout secondary), lat/lng (caption tertiary, hidden when zero).
2. **Your rating** — calls `GET /places/{place_id}/my_rating`. Three states via `myRating: PlaceRating?` + `myRatingLoaded: Bool`:
   - Loading: `ProgressView()`
   - Has rating: score pill + "You rated this X.X"
   - No rating: italic "You haven't rated this yet"
3. **Friends activity** — calls `GET /places/{place_id}/friends_activity` (TYP-65). Plain `Text` rows like "Sam rated this 8.3" / "Jess saved this". Empty state and loader handled.
4. **Actions row** — three `Button`s: Save/Unsave (functional via `POST/DELETE /saved_places/{id}` through the new `APIClient.requestVoid`), Rate + Plan (`.disabled(true)` until TYP-29 and Plan tab respectively).

Both Profile lists (`placeRatingRow`, `savedPlaceRow`) are now wrapped in `NavigationLink { PlaceDetailView(place: ...) } label: { ... }.buttonStyle(.plain)`.

---

## Locked design decisions

### 1. Bundled with TYP-65 backend; TYP-21 fix rode along

TYP-49 needed friends activity data that no existing endpoint could supply. Filed TYP-65 as a sibling backend ticket (`GET /places/{id}/friends_activity`) rather than expanding TYP-49 past its 8pt cap. Both tickets were built on the same branch but split into two PRs (#28 backend-only, #29 iOS+docs).

The TYP-21 drive-by came from end-to-end testing: `GET /places/{id}/my_rating` was 500-ing because `get_latest_for_user_place` returned a raw `PlaceRating` ORM row that didn't have `place_name` or `category`, but `PlaceRatingOut` required them. Mirrored `list_by_user`'s `JOIN Place` pattern to fix. Latent since TYP-21 shipped — TYP-49 was the first end-to-end consumer.

### 2. "Function first, polish last" build approach

Stated mid-session: "i think our goal is to get all the info down then adjust for UI looking and UX." Saved as `feedback_function_first_ui.md`. Applied for the back-half of TYP-49 — friends-activity + actions row were built unstyled to confirm the data plumbing worked before any design pass. TYP-67 filed as the dedicated polish ticket.

### 3. `Place` lat/lng = 0 sentinel for PlaceRating navigation

When tapping a Places-tab row, the caller has a `PlaceRating` — which has `placeId`, `placeName`, `category` but **no `latitude` / `longitude`**. `PlaceDetailView` takes a `Place`, so we construct one inline with `latitude: 0, longitude: 0`. The header hides the lat/lng line when both are zero:

```swift
if place.latitude != 0 || place.longitude != 0 {
    Text("\(place.latitude), \(place.longitude)") ...
}
```

Rejected alternatives:
- **Add `GET /places/{place_id}`** for full hydration → cleaner long-term but new endpoint scope; not filed yet
- **Only wire Saved-tab entry** (where Place is full) → drops half the entry points
- **Two initializers on PlaceDetailView** → more code, same problem

The sentinel is a v1 compromise. Future ticket should add the hydration endpoint.

### 4. Discriminated-union model pattern reused

`FriendsActivityItem` (in `Models.swift`) mirrors `FeedItem`'s custom-`Decodable` pattern: an enum with one case per variant, a private `DiscriminatorKey` for the `type` field, and a hand-rolled `init(from decoder:)` that switches on `type` and constructs the matching variant. This is now the established pattern for any polymorphic JSON response.

Backend side: `FriendRatingOut` and `FriendSaveOut` both carry a `type: Literal[...]` field. Pydantic and Swift agree on the wire format by hand-coordination.

### 5. `APIClient.requestVoid` added for 204 endpoints

`/saved_places/{place_id}` POST/DELETE return `204 No Content`. APIClient's existing `request<T: Decodable>` blew up trying to decode an empty body. Added a parallel `requestVoid(_:method:)` with a matching private `sendVoid` that runs the same auth/encoding/status-check logic but skips the decode step.

First iOS consumer of a 204 endpoint. Other 204 endpoints (`POST /friends/requests/{id}/reject`, `DELETE /me/friends/{id}`, etc.) can use this helper when they wire up.

### 6. `myRating` request and `friends_activity` request run sequentially

Both fetches live in the same `.task` block on the ScrollView, sequentially (not parallel via `async let`). Reasoning: low complexity, two requests is cheap, no observable UX downside on the simulator. Easy to upgrade to parallel later if needed.

### 7. `isSaved` initialized from `place.isSaved` via custom `init`

```swift
init(place: Place) {
    self.place = place
    self._isSaved = State(initialValue: place.isSaved)
}
```

`@State` defaults can't reference instance properties at declaration time, so custom init. Edge case: Places-tab navigation passes `isSaved: false` regardless of the real value (we don't have it on `PlaceRating`). User can re-save and it'll work; the cosmetic "Save" label is wrong until they tap. Same `GET /places/{place_id}` follow-up would solve this too.

---

## Known limitations (acceptable for v1)

- **Failed `my_rating` request indistinguishable from "no rating"** — both show the placeholder. Logged via `print(...)` so visible in Xcode console. Distinguishing them would need a `loadError: Error?` state, deferred.
- **Lat/lng = 0 sentinel** (see decision 3).
- **`isSaved` not refreshed on appear** (see decision 7).
- **`scorePill` / `scoreColors` / `iconName(for:)` duplicated** from `ProfileView` — second consumer; TYP-64 will extract once a third consumer surfaces (likely during TYP-67 or a future Feed tab build).

---

## Sequel tickets filed

- **TYP-65** — already merged; the backend endpoint this consumes
- **TYP-66** — attendee tracking on outings + events (came out of a product discussion mid-build: "can friend activity say *who* they went with?"). Out of scope for TYP-49; needs schema + iOS picker at outing-completion
- **TYP-67** — UI/UX polish pass; the dedicated visual layer for this screen

Not yet filed:
- `GET /places/{place_id}` endpoint for full Place hydration (would solve lat/lng sentinel + isSaved freshness)

---

## Files touched (PR #29)

```
ios/TypeA/TypeA/APIClient.swift              + requestVoid + sendVoid
ios/TypeA/TypeA/Models.swift                 + FriendRating, FriendSave, FriendsActivityItem
ios/TypeA/TypeA/Views/PlaceDetailView.swift  new file
ios/TypeA/TypeA/Views/ProfileView.swift      NavigationLink wraps around place rows
backend/app/repositories/place_ratings.py    get_latest_for_user_place: JOIN Place
CLAUDE.md                                    completed tickets + queued blocks
docs/CURRENT_HANDOFF.md                      merge entry
docs/TYP_61_HANDOFF.md                       finally landed (was uncommitted since PR #27)
```
