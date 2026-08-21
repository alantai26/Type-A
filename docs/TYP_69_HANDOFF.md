# TYP-69 Handoff — mvML-2: Hand-curated seed data

**Status:** Done (merged in PRs #34 + #35, commits `6d673aa` + `703eb5c`)
**Branch:** `typ-69-mvml-2-hand-curated-seed-data-alan`
**Estimate:** 4 pts

Part 2 of the mvML sequence. TYP-68 shipped the seed *helpers*; this ticket
shipped the *data* — a synthetic training set with a deliberately baked-in
answer key that TYP-70 and TYP-71 must recover.

---

## What shipped in this ticket

### `backend/scripts/seed_ml_data.py` (new, 195 lines)

A generator, not a fixture list. Sits on top of TYP-68's helpers
(`create_user`, `create_place`, `create_rating`, `create_outing_with_stops`)
imported from `seed_dev_data.py`.

**CLI:**

```bash
cd backend && source venv/bin/activate
python scripts/seed_ml_data.py [--seed 42] [--coverage 0.85] [--outings-per-user 5]
```

Same non-local-DB safety rail as `seed_dev_data.py` — prints the host and
demands a typed `yes` for anything that isn't `localhost` / `127.0.0.1`.

### The answer key — `PREFERENCE_MATRIX`

8 personas × 5 categories, each cell a `(low, high)` rating range:

| persona | Activity | Restaurant | Cafe | Dessert | Bar |
|---|---|---|---|---|---|
| `activity_fan` | **8–10** | 4–6 | 4–6 | 5–7 | 5–7 |
| `foodie` | 3–5 | **8–10** | 7–9 | 7–9 | 5–7 |
| `coffee_snob` | 3–5 | 5–7 | **9–10** | 6–8 | 4–6 |
| `bar_hopper` | 5–7 | 6–8 | 4–6 | 5–7 | **8–10** |
| `dessert_head` | 4–6 | 6–8 | 6–8 | **9–10** | 4–6 |
| `omnivore` | 6–8 | 6–8 | 6–8 | 6–8 | 6–8 |
| `hater` | 2–4 | 2–4 | 2–4 | 2–4 | 2–4 |
| `chill_balanced` | 6–8 | 7–9 | 7–9 | 6–8 | 5–7 |

This table **is the eval target.** TYP-70's eval script should recover each
cell's midpoint from the fitted user×category interaction terms. The two
degenerate personas are deliberate: `omnivore` (flat 6–8 across the board) and
`hater` (flat 2–4) exist to prove the model learns a *user intercept*
separately from *category preference* — a model that only learns category
effects will fail on exactly these two.

Ratings are sampled `round(random.uniform(low, high), 1)`, so within-cell noise
is uniform, not Gaussian. Irreducible error is bounded: for a 2-wide range the
best possible MAE against the midpoint is **0.5**. Anything near that is a
ceiling result, not a bug.

### Places — 26 across 5 categories

Real Boston venues, 5–6 per category (Activity 5, Restaurant 6, Cafe 5,
Dessert 5, Bar 5). Coordinates are real enough for the earthdistance indexes to
behave. Names are drawn from places Alan actually goes — the point was
plausible category assignment, not geographic uniformity.

### Generation logic

**Ratings** (`generate_ratings`) — every user × every place, gated by
`--coverage 0.85`. Coverage below 1.0 exists so the matrix is sparse, like real
data; it also gives the hold-out split something non-trivial to do.

**Outings** (`generate_outings`) — this is the part built specifically for
TYP-71. For each user, categories are ranked by preference midpoint, then each
outing pairs a **top-2 category stop at weight 0.7** with a **bottom-2 category
stop at weight 0.3**. `final_rating` is the exact weighted sum of two fresh
category samples.

That construction is the whole point: the composite rating is a *known linear
function* of per-stop contributions, so the attribution model has ground truth
to be scored against. If TYP-71's decomposition can't recover roughly
`0.7 × top + 0.3 × bottom`, the model is wrong — not the data.

### `docs/SECURITY_CONSIDERATIONS.md` (new)

Rode along, not core scope. A living security audit seeded from a 20-item
pre-launch checklist plus items surfaced during this session, grouped
✅ Have / ⚠️ Partial / ❌ Missing / N/A. Ends with 7 recommended pre-TestFlight
tickets in priority order. Explicitly notes **none of them block mvML**
(synthetic data, no external users) but all should land before TestFlight.

### `.claude/hooks/protect-files.sh` (hardened)

Previously only blocked Edit/Write by **file path**. Now has a second part that
scans outgoing **content** (`tool_input.content` for Write,
`tool_input.new_string` for Edit) against ~9 regexes: env-style assignments
carrying real values, DB URLs with embedded credentials, inline `BEGIN ...
PRIVATE KEY` blocks, `AKIA`-prefixed AWS key IDs, and a
`(API_KEY|SECRET|TOKEN|PASSWORD) = <20+ chars>` heuristic.

**Why:** on 2026-08-19 the full local `DATABASE_URL` got copied out of
`CLAUDE.md` into a session notes doc. The path-based hook happily allowed it —
the secret was moving *out of* a protected file, not into one. Both copies were
redacted (that's the one-line diffs in `CLAUDE.md`, `docs/ALEMBIC_NOTES.md`,
`docs/CURRENT_HANDOFF.md`, `docs/TYP_61_HANDOFF.md` — all now say "see `.env`"
instead of the literal URL).

An `.env.example` early-exit was added **before both parts**, because the
`\.env\.` path pattern would otherwise have matched the committed template.

---

## Resulting local DB state (verified 2026-08-21)

| table | rows | of which synthetic |
|---|---|---|
| `users` | 10 | 8 |
| `places` | 32 | 26 |
| `place_ratings` | 193 | 168 |
| `outings` | 47 | 40 |
| `events` | 94 | 80 |

Per-persona rating counts land at 19–23 (of 26 possible), consistent with 85%
coverage. The 2 non-synthetic users are Alan Tai (10 ratings) and funlego092
(15) from the TYP-58/59/60 seed rows.

---

## ⚠️ Known data-hygiene issue — read before TYP-70

**`places.category` is not a closed taxonomy.** `seed_ml_data.py` uses exactly
5 canonical values, but pre-existing seed rows introduced others:

| name | category | source |
|---|---|---|
| Trillium Brewing | `Brewery` | TYP-58 seed |
| Central Park | `park` | older seed |
| Joe's Pizza | `restaurant` | older seed |

Two separate problems:

1. **Off-taxonomy values** — `Brewery` and `park` are outside the 5 categories
   the preference matrix defines. There is no ground-truth preference for them.
2. **Case collision** — `restaurant` and `Restaurant` are distinct strings, so
   a naive category one-hot produces **two features for one concept**, and the
   lowercase one is fit on a single place with almost no ratings.

There is also a near-duplicate venue: **`Top Golf`** (TYP-58 seed) and
**`TopGolf Canton`** (ML seed) are the same real place under two names. Both
are `Activity`, so a category-only model is unaffected — but any *place-level*
term would split one venue's signal across two columns.

**TYP-70 must decide explicitly** whether to (a) normalize/`lower()` category
at feature-build time, (b) filter training rows to the 5 canonical categories,
or (c) clean the data. Do **not** let this be an accident of `pd.get_dummies`.

There is no CHECK constraint on `places.category` (unlike `status` and
`rsvp_status`, which do have them). Adding one would need a migration and a
backfill — worth filing, out of scope for mvML.

---

## Design decisions worth knowing

### Why generated ranges, not hand-typed ratings

The ticket said "hand-curated." What's hand-curated is the **preference
matrix** — the semantic claim that a coffee snob rates cafes 9–10. The
individual 193 rating values are sampled from it. Typing 193 numbers by hand
would have produced the same information content with more opportunity for
accidental structure (fatigue drift, unconscious clustering).

### `--seed 42` default

Sampling is reproducible by default. TYP-70's eval numbers are therefore
comparable across runs and across machines. Change the seed only to check the
model isn't overfit to one particular draw.

### Re-running is safe but not idempotent for ratings

Users, places, and outings are matched by natural key and skipped. **Ratings
append** (per TYP-21's append-only design; dedupe happens at read time via
`DISTINCT ON`). So a second run doubles the raw `place_ratings` rows.

This matters for TYP-70: **train on latest-per-(user, place) via `DISTINCT ON`,
not on raw rows**, or a re-run silently double-weights every observation.

### Outings are `status='completed'` with `final_rating` set

`create_outing_with_stops` writes completed outings directly rather than
walking the plan → confirm → rate lifecycle. Events get `sequence_position` and
`weight`; the creator gets an `OutingInvitation` with `rsvp_status='accepted'`
to mirror TYP-19's API retrofit. Seeded state is indistinguishable from
API-created state.

---

## Files touched

| file | change |
|---|---|
| `backend/scripts/seed_ml_data.py` | new — 195 lines, the generator + answer key |
| `docs/SECURITY_CONSIDERATIONS.md` | new — living security audit |
| `.claude/hooks/protect-files.sh` | +62/-6 — content scanning (Part 2) + `.env.example` exit |
| `CLAUDE.md` | 1 line — DB URL redacted |
| `docs/ALEMBIC_NOTES.md` | 1 line — DB name redacted |
| `docs/CURRENT_HANDOFF.md` | 1 line — DB URL + LAN IP redacted |
| `docs/TYP_61_HANDOFF.md` | 1 line — LAN IP + Tailscale IP redacted |

**Not committed:** `docs/LEARNING_MVML_SESSION.md` is referenced by
`SECURITY_CONSIDERATIONS.md:47` as the file the leaked URL landed in, but it
has no git history and isn't on disk. The reference is archaeological only.

---

## How to verify locally

```bash
cd backend && source venv/bin/activate
python scripts/seed_ml_data.py --seed 42
```

Then sanity-check that the answer key is actually present in the data — the
coffee snob should out-rate the activity fan on cafes by ~4 points:

```sql
SELECT u.display_name, p.category, round(avg(pr.rating)::numeric, 2) AS avg
FROM place_ratings pr
JOIN users u  ON u.user_id  = pr.user_id
JOIN places p ON p.place_id = pr.place_id
WHERE u.email LIKE '%@synthetic.typea.dev'
GROUP BY 1, 2 ORDER BY 1, 2;
```

Each cell should sit near its `PREFERENCE_MATRIX` midpoint.

---

## What's next

**TYP-70 (mvML-3)** — Atomic Recommender, ridge regression, 8 pts. Unblocked;
the data is in the DB and needs no regeneration.

Carry into it:
- the category-hygiene decision above (non-optional)
- `DISTINCT ON` at training-data load, not raw `place_ratings`
- MAE floor of ~0.5 from uniform within-cell sampling
- `omnivore` + `hater` are the personas that prove user-intercept learning
