# JWT Auth Understanding

Reference notes on why the auth layer is structured the way it is. Covers the Supabase + JWT decision, what each file does, and the mental model for how a request flows through it.

---

## The Problem

The backend has tables for users, events, outings, ratings. Without auth, anyone could `POST /events` with any `creator_id` and there's no way to verify who's actually making the request. Every protected feature endpoint (events, outings, predictions, comparisons) needs to know *who* the caller is. That's what TYP-17 builds.

---

## Why Supabase

Rolling your own auth is a tarpit: password hashing, reset emails, email verification, OAuth, session management, refresh tokens, rate limiting, account recovery. Weeks to do badly, months to do safely.

Supabase handles all of that. The deal:

1. User logs in via Supabase.
2. Supabase returns a **JWT** (JSON Web Token).
3. Client sends that JWT on every API request.
4. Backend verifies the JWT and trusts what it says.

Our job shrinks to: *verify the JWT is genuine, then look up the matching user row.*

---

## What a JWT Is

A string with three dot-separated chunks: `header.payload.signature`.

- **payload** — a JSON blob like `{"sub": "<uuid>", "email": "alan@..."}` describing the user.
- **signature** — cryptographic proof that Supabase signed this exact payload. Tampering breaks the signature.

The key property: you can verify the signature **without calling Supabase** — you just need their public key. Supabase publishes it at:

```
{SUPABASE_URL}/auth/v1/.well-known/jwks.json
```

This is the **JWKS** (JSON Web Key Set). Fetch once, cache it, use it to verify any future JWT. Zero network round-trips to Supabase per request.

---

## Each File and Why It Exists

### `app/auth.py` — the JWT verifier

| Symbol | Purpose |
|---|---|
| `_jwks_client` | Caches Supabase's public key. Doesn't refetch every request. |
| `_validate_token` | Verifies signature + `audience="authenticated"`. Anything wrong → 401. |
| `_provision_user` | Solves the **first-login problem**. Supabase has its own user table; we have ours (with `display_name`, FKs, etc.). They don't sync. First time a user hits the API, their row in *our* `users` table doesn't exist yet — so we create one from the JWT's `sub` (their Supabase UUID) and `email`. |
| `require_auth` | **The reusable FastAPI dependency.** This is the ticket's payoff. |

`require_auth` lets every future protected route do this:

```python
def create_event(body: EventCreate, current_user: User = Depends(require_auth)):
    ...
```

FastAPI runs `require_auth` first. If the token is missing/forged/expired/malformed, the request 401s before the route body executes. Inside the route you have a guaranteed-valid `User` object.

### `app/db.py` — the DB session dependency

Every endpoint that touches Postgres needs an open SQLAlchemy session. `get_db` is a generator dependency: opens a session, yields it, closes it after — even if the route raises. Standard SQLAlchemy + FastAPI pattern. Inject alongside `require_auth`.

### `app/schemas/users.py` — Pydantic shapes

Separates *DB representation* from *wire representation*.

- `UserOut` — what the API returns.
- `UserUpdate` — what `PATCH /me` accepts.

Keeps the SQLAlchemy `User` object from leaking directly over HTTP, which would expose internal fields whenever the model grows.

### `app/repositories/users.py` — DB query helpers

Per the layered architecture in CLAUDE.md: routes shouldn't write SQL directly. Routes call services/repos; repos own DB calls. `update_user` is trivial today — once logic accumulates ("only allow display_name change once a week," joins, etc.) it stays in one place instead of bleeding into route handlers.

### `app/routes/users.py` — `/me` endpoints

- `GET /me` — answers "who am I?" Used by clients for profile pages, settings screens, token-validity checks.
- `PATCH /me` — updates `display_name`.

`/me` doubles as the **smoke test** for the entire auth pipeline. If `/me` returns 200 with a valid token and 401 without, every layer (JWKS fetch, signature verify, claim parse, user provision, DB session) is working.

### Plumbing

- `main.py` — `load_dotenv()` so `os.environ["SUPABASE_URL"]` resolves at import time, registers the users router.
- `requirements.txt` — `pyjwt[crypto]==2.8.0`. The `[crypto]` extra installs the libs needed for **ES256**, the asymmetric algorithm Supabase signs JWTs with.
- `.env.example` — `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`.

---

## Request Flow (Mental Model)

```
Client (iOS / curl) → Supabase login
                    ← JWT

Client → GET /me  (Authorization: Bearer <jwt>)

  Backend:
    1. require_auth dependency runs first
    2. JWT signature verified against cached Supabase public key
    3. sub + email extracted from JWT payload
    4. User row looked up (or created on first login)
    5. User object injected into the route as `current_user`
    6. Route logic runs, knowing exactly who is calling
```

Every future protected endpoint is just step 6. TYP-17 paid for steps 1–5 once, forever.

---

## Why 401 (not 500) on Invalid Token

A malformed or forged JWT is a **client problem**, not a server problem. 500 implies "server bug" and floods logs with stack traces that look like emergencies but aren't. 401 ("Unauthorized") tells the client "your credentials aren't valid — re-authenticate." That's why `_provision_user` wraps `uuid.UUID(sub)` in try/except: a non-UUID `sub` claim is bad input, not a server failure.

The general rule: catch *specific* expected exceptions (`ValueError` here) and translate them to the right HTTP status. Let unexpected exceptions (DB outage, etc.) bubble up as 500 — those genuinely are server bugs.
