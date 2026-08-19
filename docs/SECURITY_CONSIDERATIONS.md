# Security Considerations

Living audit of TypeA's security posture. Grouped by status:
- ✅ **Have** — implemented and verified (or verifiable)
- ⚠️ **Partial** — some coverage, needs audit or completion
- ❌ **Missing** — real gap; ticket-worthy
- **N/A** — checklist item that doesn't apply to this stack

Original 20-item checklist from a "20 things to have Claude do before launching your app" TikTok (2026-08-19), plus items surfaced during the mvML security discussion.

---

## ✅ Have

- **Hide API keys** — `.env` file is gitignored; contains `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`. `.claude/hooks/protect-files.sh` blocks Claude from editing `.env`, `.git/`, credentials.
- **Use public DB key** — iOS carries only the Supabase publishable (anon) key. Server has no `service_role` key.
- **Enforce server-side auth** — `require_auth` FastAPI dependency on every protected route (`app/auth.py`). JWTs verified via cached JWKS (ES256 signatures). No client-side-only trust of `sub`/`email` claims.
- **Block field tampering** — Pydantic request schemas define exactly which fields are accepted; unknown fields rejected. `PATCH /me` only takes `display_name` / `bio` — client cannot spoof `user_id` or `created_at`.
- **Parameterize queries** — SQLAlchemy ORM parameterizes everything. Raw `text()` queries in `app/repositories/places.py` and `saved_places.py` (for earthdistance) use `:name` bind params, not string interpolation.
- **Validate all input** — Pydantic on every request body. `max_length=160` on `bio`. Enum validation on `rsvp_status`, `status`. Type coercion at the boundary.
- **Force HTTPS** — Render terminates TLS on `type-a-api.onrender.com`. Local dev runs HTTP for the iOS simulator, which is fine (LAN-only).

## N/A (bearer-token JSON API + Supabase auth)

- **Encrypt sensitive data** — Render Postgres does at-rest encryption by default; TLS in transit; no PII beyond bio/display_name/email. No credit cards, no health data.
- **Secure session cookies** — no cookies; bearer tokens only.
- **Hash passwords** — Supabase handles password storage entirely; server never sees plaintext or hashes.
- **Rate limit login** — same, Supabase rate-limits its own `/token` endpoint.
- **Escape user content** — API returns JSON, not HTML. SwiftUI `Text` is XSS-safe. Would apply if a web client ever ships.
- **Restrict file uploads** — no file uploads. Google Places integration fetches metadata, doesn't upload.

## ⚠️ Partial

- **Lock record access** — most endpoints check `creator_id == caller_id` (outings, events, ratings). But `GET /outings/{outing_id}/predict` explicitly has no ownership check (documented in `CLAUDE.md` under the endpoint catalog). No formal cross-user authz audit exists. **Needs**: systematic sweep of every route asking "can I access this by guessing the resource ID as a different user?"
- **Trim API responses** — Pydantic response schemas define fields, no accidental over-exposure of column data. But `/me/friends` returns `display_name` + `created_at` — fine. `UserOut` returns `email` — also fine since it's only returned to the caller for their own row. Worth a formal audit before public launch to make sure no cross-user endpoint accidentally leaks another user's email.

## ❌ Missing

- **Purge Git secrets** — `.env` should never have been committed but nobody has actually verified. **Action**: `git log --all --full-history -- backend/.env` + a `trufflehog` or `gitleaks` scan on full history.
- **Enable row-level security** — Postgres RLS is not configured. Authorization is app-layer only (`WHERE user_id = caller` in every query). Real defense-in-depth gap, but common for non-Supabase-DB FastAPI apps. Adding RLS would require every ORM query to run under a session variable set to the current user, then policies on every table. Not trivial.
- **Add bot protection** — no captcha, no bot detection. Fine pre-TestFlight since Apple gates the download. Becomes relevant if signup ever opens on the web.
- **Add security headers** — no `X-Content-Type-Options: nosniff`, no `Strict-Transport-Security`, no `Referrer-Policy`. Render may set some defaults — worth `curl -I https://type-a-api.onrender.com/health` to confirm. FastAPI middleware fix is ~5 lines: `app.add_middleware(SecurityHeadersMiddleware, ...)`.
- **Scan dependencies** — no `pip-audit`, `safety`, Dependabot, or Renovate. `requirements.txt` is pinned but nothing checks for CVEs. Fix: add GitHub Dependabot config (one YAML file).

## Additional items (not on the checklist but surfaced during audit)

- **Rate limiting on our own endpoints** — nothing prevents:
  - `POST /place_ratings` spam (data pollution → poisons ML training)
  - `POST /friends/requests` spam (harassment vector)
  - `POST /events` or `POST /outings` spam (DB bloat)
  - Brute-force resource-ID enumeration (`GET /outings/{id}` with random UUIDs — bounded by UUID entropy but still)
  - Fix: `slowapi` or Redis-backed limiter, ~10 lines to add per-route.
- **CORS allowlist** — verify `main.py`'s CORS middleware doesn't use `allow_origins=["*"]` in production. Should be pinned to iOS bundle IDs (bearer-token APIs don't strictly need CORS, but browsers of debug tools might).
- **JWT expiry handling** — Supabase JWTs auto-refresh on the client via the SDK. Server enforces `exp` claim via `pyjwt` defaults. Good.
- **Secrets rotation runbook** — no documented process for rotating `SUPABASE_PUBLISHABLE_KEY` or `DATABASE_URL` if compromised. Not urgent, but worth writing.

---

## Recommended pre-TestFlight tickets

Rough priority order:

1. **Git secret purge audit** — `git log --all -- .env` + `gitleaks` scan. Non-negotiable before any external user.
2. **Security headers middleware** — `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`. ~5 lines of FastAPI middleware.
3. **Dependabot config** — one YAML file, GitHub does the rest.
4. **Rate limiting** on `POST /place_ratings` and `POST /friends/requests`. `slowapi` integration.
5. **Cross-user authz audit** — systematic route sweep; document any endpoint where a caller can read/mutate another user's data.
6. **CORS allowlist verification** — confirm no `*` in production.
7. **Postgres RLS** — larger, defense-in-depth. Only if you want belt-and-suspenders.

**None of these block mvML** (synthetic data + no external users). Do them before TestFlight (post-mvML).
