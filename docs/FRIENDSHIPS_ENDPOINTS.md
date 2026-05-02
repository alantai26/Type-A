# Friendships Endpoints (TYP-22)

What got built, why, and what was learned. Companion to `RATING_ENDPOINTS.md`.

---

## Endpoints added (6)

| Method | Path | Notes |
|---|---|---|
| POST | `/friends/requests` | body=`FriendRequestCreate`. Idempotent on existing `(me, them)`. Auto-accepts if reverse pending exists. 422 on self-friend. |
| POST | `/friends/requests/{user_id}/accept` | Mutates pending row → accepted, inserts mirror row, single commit. 404 if no pending, 409 if already accepted. |
| POST | `/friends/requests/{user_id}/reject` | 204. Hard-deletes the pending row. 404 if no pending, 409 if already accepted. |
| DELETE | `/me/friends/{user_id}` | 204. Single OR-filter `.delete()` removes both rows atomically. 404 if `deleted == 0`. |
| GET | `/me/friends` | Hydrated list (user_id, display_name, created_at) for accepted friends. ORM JOIN to `users`. |
| GET | `/me/friend_requests` | Hydrated list of incoming pending requests. Mirror of `/me/friends` — flips which side filters/joins. |

All require Bearer JWT.

## Files touched

```
backend/app/schemas/friendships.py        new — FriendRequestCreate, FriendshipOut, FriendOut
backend/app/repositories/friendships.py   new — get / create_pending / delete_one / list_friends_for_user / list_pending_for_user
backend/app/services/friendships.py       new — request / accept / reject / unfriend
backend/app/routes/friendships.py         new — 6 endpoints
backend/app/main.py                       modified — wired friendships router
```

No migration. No model changes. The `friendships` table + CHECK constraint were already in place from TYP-8.

---

## Locked design decisions

### 1. Option A: 1 row pending, 2 rows accepted

A pending request is a single `(requester, recipient, 'pending')` row. Direction is recoverable: `user_a_id` = requester. On accept, the row is mutated to `'accepted'` and a mirror `(recipient, requester, 'accepted')` row is inserted in the same transaction.

Rejected: Option B (always two rows, symmetric) was considered. Lost out because pending is *inherently asymmetric* — one party asked, one hasn't decided. Two rows would either lose direction or require a `requested_by` column, defeating the point of symmetry.

### 2. Hard delete on reject (not soft)

Reject removes the pending row entirely. No `status='rejected'` write.
- **Pro:** simpler. No zombie rows. Re-request after rejection is identical to a first-time request — same code path.
- **Con:** rejected user can re-spam. No throttle. Acceptable for MVP.

The schema's CHECK constraint still allows `'rejected'` as a value, so flipping to soft-reject later doesn't require a migration.

### 3. Idempotent duplicate POST

`POST /friends/requests` for an already-pending or already-accepted `(me, them)` row returns the existing row (200) instead of erroring. The client doesn't have to distinguish "first request" vs "re-request" UX paths.

### 4. Auto-accept on mutual pending

If A sends B a request and B already had a pending request out to A, the second POST auto-accepts. The existing `(B, A, 'pending')` row is mutated to `'accepted'` and the mirror `(A, B, 'accepted')` is inserted in the same call.

Avoids a stuck state where both users have outgoing requests neither side knows to accept. Treated as mutual interest = consummated friendship.

### 5. Block self-friend

`POST /friends/requests` with `recipient_id == current_user.user_id` → 422. Caught at the service layer before any DB query.

### 6. Unfriend deletes both rows in one atomic statement

```python
db.query(Friendship).filter(
    or_(
        and_(user_a_id == me, user_b_id == them),
        and_(user_a_id == them, user_b_id == me),
    )
).delete(synchronize_session=False)
```

Returns the row count. If `0` → 404. Otherwise commit. Single round-trip beats two `delete_one` calls — atomic, no risk of half-deleted friendship if one succeeds and the other errors.

### 7. Service layer holds multi-row transactions

`accept` and `unfriend` mutate or delete more than one row. Following the TYP-21 pattern: don't compose repo helpers (each commits independently) — instead mutate ORM objects directly in the service and call `db.commit()` once at the end. Repos stay dumb (one commit per function).

### 8. Param naming reflects layer concerns

- Repo: `user_a_id` / `user_b_id` (matches column names).
- Service `request`/`accept`/`reject`: `requestor_id` / `recipient_id` (semantic — there *is* a sender and receiver).
- Service `unfriend`: `user_id` / `other_id` (symmetric — neither side is sender/receiver).

The renaming makes intent explicit at each layer boundary.

### 9. Hydrated `Out` schemas for list endpoints

`FriendOut` returns `(user_id, display_name, created_at)` — the *other* person's user info plus when the friendship row was created. Built via ORM JOIN, no second round-trip from the iOS client to fetch names.

`FriendshipOut` (raw row shape: `user_a_id`, `user_b_id`, `status`, `created_at`) is used for POST responses where echoing the resulting row is more useful than hydrating it.

`email` was deliberately dropped from `FriendOut` — display_name is what the UI shows, and there's no reason to leak emails through the friends list.

### 10. POST for verbs, 204 for empty bodies

Following the TYP-19 convention: status changes (`/accept`, `/reject`) are POSTs to named-action paths, not PATCHes with a `status` field. Reject and unfriend return 204 No Content because they have nothing meaningful to return.

---

## Concepts learned (Alan-side notes)

### Composite-PK direction encoding
With Option A, "which side am I on" tells you who I am to this friendship:
- `user_a_id == me` → I'm the requester (or, after accept, the row I "own")
- `user_b_id == me` → I'm the recipient (a request was sent to me)

The mirror in `list_friends_for_user` vs `list_pending_for_user` is mechanical: same query shape, swap which side filters, swap which side joins to `users`.

### SQLAlchemy ORM JOINs
```python
db.query(User.user_id, User.display_name, Friendship.created_at)
  .join(Friendship, Friendship.user_b_id == User.user_id)
  .filter(Friendship.user_a_id == user_id, Friendship.status == "accepted")
  .all()
```
Returns `list[Row]`. `Row._mapping` is dict-like, so `FriendOut.model_validate(row)` works directly when the schema has `from_attributes=True`.

### `or_` and `and_` for boolean SQL trees
Python's `or`/`and` short-circuit on truthiness — they can't build a SQL expression tree. SQLAlchemy provides `or_(...)` / `and_(...)` (functions, not keywords) to construct the AST.

### `.delete()` returns the affected row count
Lets you skip a separate "does this row exist?" lookup. Combine with a 404 raise on `count == 0`:
- One round-trip instead of two
- Atomic — either all rows that match get deleted or none do
- `synchronize_session=False` skips ORM reconciliation; faster, fine when you don't reuse the in-memory objects

### Keyword-only args (`*,`)
Forces every arg after it to be passed by keyword. Used at the repo layer where two args have the same type (two `uuid.UUID`s) — prevents silent swap bugs.

### Defaults vs declarations
In `def f(user_a_id=requestor_id)`, `requestor_id` is evaluated *at function-definition time* as a default value. If the name doesn't exist in scope, `NameError` immediately at import. To declare a parameter, use `name: type` (no `=`).

### FastAPI path-param binding
Path params bind to function args **by name, not position**. `{user_id}` in the path requires `user_id:` in the function signature; renaming one without the other yields a 422 "missing path parameter."

### `response_model` vs return-type annotation
`response_model=...` on the decorator is the *contract* — FastAPI uses it for serialization and OpenAPI generation. The function's return-type annotation (`-> Friendship`) is informational (IDE/typing). The two should agree but they don't have to be identical (return raw ORM, decorator serializes via the schema).

### Service-vs-repo on multi-row transactions (reinforced from TYP-21)
- Repos commit per call. Composing two repo helpers in a service breaks atomicity (two commits, no rollback if the second fails).
- For `accept`: mutate the existing pending row, build a new `Friendship(...)` object, `db.add(mirror)`, `db.commit()`, `db.refresh(mirror)`. One commit.
- For `unfriend`: single ORM-built DELETE with OR clause + `db.commit()`. One round-trip.

---

## Open issues / what's not done

### 1. No manual end-to-end testing
None of the 6 endpoints have been hit with a real request. Same risk as TYP-21: trivial bugs (typos, schema mismatches) shipping to PR.

### 2. No outgoing-request endpoint
The Linear ticket only lists `GET /me/friend_requests` (incoming). No way to view or rescind requests *I've* sent. If iOS needs it, add `GET /me/friend_requests/outgoing` and `DELETE /friends/requests/{user_id}` (rescind).

### 3. No re-spam throttle
Hard-delete on reject means a rejected user can re-request immediately. If MVP usage shows abuse, two options: flip reject to soft-delete (sets `status='rejected'`, blocks future requests until cleared) or add a separate cooldown table.

### 4. `'rejected'` status value never written
The CHECK constraint allows it, but no code path writes it. If a future change adds soft-reject, the constraint already accommodates the new value — no migration needed.

### 5. Half-friendship not detectable
If for any reason only one of the two accepted rows exists (data corruption, partially-failed unfriend), the schema doesn't surface it as inconsistent. `list_friends_for_user` would silently miss the friend. No active mitigation.
