# ML + Rating Understanding

Conceptual notes from a teaching session — clarifies how the rating columns and ML predictions actually fit together. Read this before touching `derived_score`, `attribution_outputs`, or `events.weight`.

---

## Features vs. Predictions

Easy to conflate, but distinct:

- **Features** = inputs to the model (place category, companions, time of day, weather, etc.)
- **Prediction** = the number the model outputs ("7.5 for TopGolf")

Category-based bias (e.g. "Alan prefers activity > restaurant") is a **feature**, not a stored field. The model learns it implicitly from `places.category` during training. No separate "category bias" column needed.

---

## Where Predictions Live: Three Compute Tiers

| Cost | Strategy | Example |
|---|---|---|
| Cheap (one inference call against trained model) | Compute live | Place rec score, outing prediction during planning |
| Expensive (refit regression across all user history) | Store, recompute periodically | `attribution_outputs` |
| Snapshot-with-meaning (preserve a moment in time) | Store and **never** overwrite | `outings.derived_score` |

Storing more numbers in the DB does not make a system "more ML." ML rigor comes from feature richness, retraining cadence, evaluation, and training signal quality. Calibration (snapshot tier) is the actual ML-engineering practice that justifies storing predictions.

---

## The Three Rating-Adjacent Columns

These three columns are easy to conflate. They do different jobs.

| Column | Job | Mutable? |
|---|---|---|
| `attribution_outputs.attributed_effect` | Learned per-place effect ("golf makes outings better"). Per-user, per-place. | Recomputed on model retrain |
| `outings.derived_score` | Prediction at outing commit time, kept for calibration | **Never overwritten** |
| `events.weight` | User's per-stop slider input when rating an outing | Set once when rating |

---

## Concrete Timeline (TopGolf + Jake's house outing)

**Friday 5pm — user commits to the outing**
- Model runs prediction: 7.8
- `outings.derived_score = 7.8` ← frozen forever

**Saturday 1am — user rates it**
- `outings.final_rating = 9.0`
- `events.weight`: TopGolf 0.7, Jake's house 0.3 (slider)
- Calibration data point exists: predicted 7.8, actual 9.0, error +1.2.
  *This only exists because `derived_score` was not overwritten.*

**Tuesday — batch retrain**
- Attribution model fits across all rated outings
- Updates `attribution_outputs.attributed_effect[TopGolf] = +1.8`
- ← This is where "golf makes outings better" actually lives

**Wednesday — user plans a new outing with TopGolf**
- New `outings` row. Live `/predict_outing` uses updated `attribution_outputs` → 8.4
- New row's `derived_score = 8.4`. Friday's outing still says 7.8. Untouched.

---

## Display Layer

- **Place detail screen** (Beli-style rec score): live `/predict_place` call, no companion context required at display time. Companions can still be features used during training.
- **Plan tab during outing assembly** (2+ events): live `/predict_outing` for the in-progress prediction. This is *not* `derived_score` — that only gets written at commit.
- **Committed outing**: snapshot `derived_score` frozen for calibration.

---

## Why Calibration Matters

If `derived_score` updates whenever anything changes, you can't calibrate — by the time you compare it to `final_rating`, the stored prediction has already drifted toward reality. Nothing left to evaluate.

Frozen snapshots enable:
- Drift detection (predictions consistently off in one direction)
- Deliberate tuning instead of blind retrains
- User-facing trust signals ("we predicted 7.5, you rated 8 — last 20 predictions averaged ±0.6 error")
- A real eval pipeline

---

## Outing Lifecycle: Confirm / Unconfirm Cycle

**States:** `planning_in_progress` ↔ `confirmed` → `completed` (plus `cancselled`)

Note: `draft` was renamed to `planning_in_progress` to better reflect the active editing phase. The cycle works like this:

1. User builds outing (state = `planning_in_progress`). Stops added/removed freely. Live `/predict_outing` shows the in-progress prediction. Nothing stored.
2. User confirms (state → `confirmed`). `derived_score` snapshotted using the model's current state and the outing's current stop list.
3. Plans change → user **unconfirms** (state → `planning_in_progress`). The previously written `derived_score` becomes stale but stays in the row temporarily.
4. User edits stops (only allowed while in `planning_in_progress`).
5. User reconfirms (state → `confirmed`). `derived_score` is **overwritten** with the new prediction.
6. Outing happens → state → `completed`. User rates → `final_rating`. Calibration uses the latest `derived_score` (from the most recent confirm) vs. `final_rating`.

**The rule:** `derived_score` is only ever (re)written at the transition *into* `confirmed`. Editing stops requires unconfirming first — that gates the schema, not just the UI.

This keeps calibration apples-to-apples: the snapshot represents what the model thought when the user committed to the outing as it actually played out. Old snapshots from earlier confirm cycles are intentionally discarded — only the prediction matching the actual outing shape is useful for evaluation.