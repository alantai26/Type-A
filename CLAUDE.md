# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Type A** — social planner iOS app that predicts how much you'll enjoy a night out based on past ratings. Closed-loop feedback: predict → commit → rate → learn → better prediction.

Two ML systems:
- **Atomic Recommender:** Ridge regression predicting individual plan ratings (1-10) with confidence intervals
- **Attribution Model:** Hierarchical regression decomposing multi-stop night ratings into per-place contributions

## Commands

```bash
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # localhost:8000, docs at /docs
alembic upgrade head                       # run migrations
alembic revision --autogenerate -m "msg"   # create migration after model changes
```

No test framework or linter configured yet.

## Architecture

Layered: **Route → Service → Repository → Database**

- `app/main.py` — FastAPI entry point, CORS middleware, root routes
- `app/routes/` — API endpoint definitions (request handling only)
- `app/services/` — Business logic
- `app/repositories/` — Data access layer
- `app/models/` — SQLAlchemy ORM models + Pydantic schemas

## Data Model

```
users(id, email, display_name, created_at)
places(id, name, lat, lng, category, source_url, google_place_id)
plans(id, creator_id, place_id, status, scheduled_for, completed_at, night_id, sequence_position, final_rating, derived_score)
nights(id, creator_id, status, scheduled_for, completed_at, final_rating, derived_score)
comparisons(user_id, item_a_id, item_b_id, item_type, winner_id, created_at)
plan_invitations(plan_id, invitee_user_id, rsvp_status, ics_sent_at)
```

Key design: plans are atomic, nights are optional multi-stop groupings, comparisons are polymorphic (plans or nights).

## Planned API Endpoints

```
GET    /health           → server status
GET    /plans            → list plans
POST   /plans            → create plan
GET    /plans/{id}       → get plan
PATCH  /plans/{id}       → update plan
DELETE /plans/{id}       → delete plan
GET    /predict_plan     → ML prediction
POST   /comparisons      → head-to-head ranking
```

## Stack

- **FastAPI** + Pydantic v2 (validation) + Uvicorn (ASGI server)
- **SQLAlchemy 2.0** ORM + **Alembic** migrations + **psycopg 3** driver
- **PostgreSQL** (`type_a_dev` on localhost:5432)
- **scikit-learn / statsmodels** for ML inference endpoints
- **Supabase or Clerk** for auth (planned)
- **Google Places API** for place metadata

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — Application secret
- `SUPABASE_URL` / `SUPABASE_KEY` — Auth provider credentials

## Git Workflow

Branches: `main` → `dev` (active development) → `prod` (release snapshots). Feature branches off `dev`, named like `TYP-8-database-schema`. PRs target `dev`. Commit messages prefixed with ticket ID (e.g. `TYP-8: ...`), include `Fixes TYP-X` to auto-close Linear tickets.
