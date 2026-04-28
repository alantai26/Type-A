# Type A Project — Complete Summary for Handoff

## Project Overview

**Type A** is a social planner iOS app that predicts how much you'll enjoy a night out based on your past ratings.

**One-sentence pitch:** The social planner that learns what makes a great plan for you, then predicts how the next one will go before you commit.

**Timeline:** 6 weeks, solo build, 10+ hrs/week

**Audience:** Alan + 5-10 friends from FirstByte/NU, eventually broader Northeastern friend group

---

## What Makes Type A Special

1. **Closed-loop feedback:** Predict → commit → rate → learn → better prediction
2. **Two ML systems:**
   - **Atomic Recommender:** Predicts individual plan ratings (Ridge regression)
   - **Attribution Model:** Decomposes multi-stop night ratings into per-place contributions (hierarchical regression)
3. **Differentiated from Beli:** Beli rates post-hoc, Type A predicts pre-commit
4. **User-facing ML:** Predicted scores with confidence intervals shown in planning UI

---

## Tech Stack

**Frontend:**
- iOS / SwiftUI
- MapKit, CoreLocation

**Backend:**
- FastAPI (web framework)
- SQLAlchemy (ORM)
- Alembic (database migrations)
- PostgreSQL (database)

**ML:**
- scikit-learn / statsmodels
- Jupyter notebooks
- FastAPI inference endpoints

**Auth & Hosting:**
- Supabase or Clerk (auth)
- Fly.io or Railway (backend deployment)
- Supabase or Neon (managed Postgres)

**Other:**
- Google Places API (place metadata)
- Claude/GPT (LLM extraction)
- Resend/SendGrid (calendar invites)
- OneSignal/Firebase (push notifications)

---

## Project Structure

```
type-a/
├── backend/
│   ├── app/
│   │   ├── main.py              (FastAPI entry point) ✅ DONE
│   │   ├── models/              (SQLAlchemy models) — TODO
│   │   ├── repositories/        (DB access layer) — TODO
│   │   ├── routes/              (API endpoints) — TODO
│   │   ├── services/            (business logic) — TODO
│   │   └── __init__.py
│   ├── migrations/              (Alembic) — TODO
│   ├── requirements.txt          ✅ DONE
│   ├── .env                      ✅ DONE (local only)
│   └── .env.example              ✅ DONE (template)
├── ios/
│   ├── TypeA.xcodeproj/         — TODO
│   └── TypeA/
├── eval/
│   ├── README.md                (ML methodology) — TODO
│   ├── notebooks/
│   │   ├── atomic_recommender.ipynb — TODO
│   │   └── attribution_model.ipynb — TODO
│   ├── plots/                   — TODO
│   └── coefficients/            — TODO
├── fixtures/
│   ├── users.json               — TODO
│   ├── places.json              — TODO
│   ├── plans.json               — TODO
│   └── seed.py                  — TODO
├── README.md                     ✅ DONE
├── .gitignore                    ✅ DONE
└── .github/workflows/           (CI/CD) — TODO (optional)
```

---

## Current Progress

### ✅ Completed (Week 0 Setup)

**TYP-5: GitHub Setup**
- Created `dev` and `prod` branches
- Set up branch protection (require PR approval before merging)
- Created folder structure
- Added .gitignore

**TYP-6: Requirements Gathering**
- Understood project scope
- Identified ML algorithms
- Clarified product differentiation

**TYP-7: Postgres + FastAPI Skeleton** ✅ MERGED
- Set up PostgreSQL locally (`type_a_dev` database)
- Installed Python dependencies (fastapi, uvicorn, sqlalchemy, psycopg, etc.)
- Created FastAPI `app/main.py` with:
  - `/health` endpoint
  - `/` root endpoint
  - CORS middleware configured
  - Automatic Swagger docs at `/docs`
- Server running on `localhost:8000` ✅

### ⏳ Next Up

**TYP-8: Database Schema (Alembic + SQLAlchemy)**
- Define SQLAlchemy models: users, places, plans, nights, comparisons
- Initialize Alembic for migrations
- Create and run first migration
- Verify tables in Postgres

**TYP-9-15:** CRUD endpoints, iOS skeleton, comparisons, synthetic data
**TYP-16-19:** ML models (atomic recommender + attribution model)
**TYP-20-31:** Plan flow, calendar invites, polish, demo, writeup

---

## Key Concepts (For New Chat Reference)

### What is a Framework? (FastAPI)

A framework abstracts away low-level networking code so you can focus on business logic.

**Without FastAPI:** 100+ lines to handle sockets, parse HTTP, validate data
**With FastAPI:** 4 lines with a decorator and function

Benefits:
- Automatic validation (Pydantic)
- Auto-generated docs (Swagger at `/docs`)
- Type hints for clarity
- Error handling built-in

---

### What is an API?

**API = Application Programming Interface**

A set of endpoints (URLs) your server responds to. Like a restaurant menu.

**Type A API endpoints:**
```
GET /health              → Server status
GET /plans               → Get all plans
POST /plans              → Create new plan
GET /plans/{id}          → Get one plan
PATCH /plans/{id}        → Update plan
DELETE /plans/{id}       → Delete plan
GET /predict_plan        → ML prediction
POST /comparisons        → Head-to-head ranking
```

---

### HTTP Requests (GET, POST, PATCH, DELETE)

**HTTP = HyperText Transfer Protocol**

The language computers use to communicate. Four main methods = CRUD operations:

| Method | Operation | Example |
|--------|-----------|---------|
| GET | Read | `GET /plans` → get all plans |
| POST | Create | `POST /plans` → create new plan |
| PATCH | Update | `PATCH /plans/5` → update plan #5 |
| DELETE | Delete | `DELETE /plans/5` → delete plan #5 |

---

### API Request vs HTTP Response

**API Request:** What the client sends to the server
```
POST /plans HTTP/1.1
Content-Type: application/json

{"place": "Top Golf", "date": "2025-04-28", ...}
```

**HTTP Response:** What the server sends back
```
HTTP/1.1 200 OK
Content-Type: application/json

{"id": 42, "place": "Top Golf", "status": "upcoming"}
```

The HTTP Response includes:
- Status code (200 = success, 422 = validation error, 404 = not found)
- Headers (Content-Type, etc.)
- Response body (usually JSON)

---

### How JSON Flows Through Your API

1. **iOS app sends POST request** with JSON body
   ```json
   {"place": "Top Golf", "date": "2025-04-28", "time": "18:00", "companions": ["Sarah"]}
   ```

2. **Uvicorn receives** the HTTP request (listening on localhost:8000)

3. **FastAPI routes it** to your endpoint handler
   ```python
   @app.post("/plans")
   def create_plan(plan: PlanCreate):
   ```

4. **FastAPI parses JSON** → Python dict → Pydantic model (`PlanCreate`)
   - Validates types (place is string? companions is list? etc.)
   - Automatically returns 422 error if invalid

5. **Your function receives validated object**
   ```python
   def create_plan(plan: PlanCreate):
       # plan.place = "Top Golf" (str)
       # plan.companions = ["Sarah"] (list)
   ```

6. **Your function does logic** (save to database)

7. **Your function returns dict**
   ```python
   return {"id": 42, "place": "Top Golf", "status": "upcoming"}
   ```

8. **FastAPI converts dict → JSON string**
   ```python
   import json
   json_string = json.dumps(return_dict)
   # '{"id":42,"place":"Top Golf","status":"upcoming"}'
   ```

9. **Uvicorn wraps in HTTP response**
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json
   
   {"id":42,"place":"Top Golf","status":"upcoming"}
   ```

10. **iOS app receives**, parses JSON, displays to user

---

### Virtual Environments (`venv`)

**Virtual environment = isolated Python workspace**

Without venv: All projects share same Python + packages (conflicts)
With venv: Each project has its own Python + packages (no conflicts)

```bash
python -m venv venv          # Create venv
source venv/bin/activate     # Activate (shows (venv) in prompt)
pip install -r requirements.txt
```

---

### Dependencies & `requirements.txt`

**Dependencies = external code libraries your project needs**

Type A requires:
- `fastapi` — web framework
- `uvicorn` — ASGI server (runs FastAPI)
- `sqlalchemy` — ORM (Python ↔ database)
- `psycopg` — PostgreSQL driver
- `python-dotenv` — reads `.env` files
- `alembic` — database migrations
- `pydantic` — data validation

```bash
pip install -r requirements.txt  # Install all at once
```

**Why list them:** Reproducibility. Anyone can run `pip install -r requirements.txt` and get exact same versions.

---

### Uvicorn (The Server)

**Uvicorn = ASGI web server**

What it does:
1. Listens for HTTP requests on a port (localhost:8000)
2. Passes requests to FastAPI
3. Receives responses from FastAPI
4. Sends responses back to clients

**Uvicorn ≠ the API.** FastAPI is the API (your code). Uvicorn is the server that runs it.

**Analogy:**
- FastAPI = recipe (your code)
- Uvicorn = oven (infrastructure)

---

### Pydantic (Auto-Validation)

**Pydantic = automatic data validation**

Define a model with types:

```python
from pydantic import BaseModel

class PlanCreate(BaseModel):
    place: str
    date: str
    time: str
    companions: list[str]
```

FastAPI automatically:
- Checks all fields are present
- Validates types (place is string, companions is list)
- Returns 422 error if invalid
- Converts JSON → model instance

**Without Pydantic:** You'd write 50+ lines of validation code
**With Pydantic:** 5 lines to define the model, zero validation code

---

### Swagger (Auto-Generated Docs)

**Swagger = interactive API documentation**

Visit `http://localhost:8000/docs` to:
- See all endpoints
- See request/response formats
- **Test endpoints directly** (click "Try it out")

FastAPI generates this automatically from your code. No extra work needed!

---

## GitHub Workflow

### Branch Strategy

```
main (bootstrap state, untouched after initial setup)
  ↓
dev (active development, all work here)
  ├── feature branch 1 (TYP-7-postgres-fastapi-skeleton)
  ├── feature branch 2 (TYP-8-database-schema)
  └── ...
  ↓
prod (release snapshots, merge from dev weekly)
```

### Commit & PR Workflow

1. **Create feature branch from dev:**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b TYP-8-database-schema
   ```

2. **Code and commit:**
   ```bash
   git add .
   git commit -m "TYP-8: Database schema setup

   - Created SQLAlchemy models
   - Initialized Alembic
   - First migration created

   Fixes TYP-8"
   ```

3. **Push and create PR on GitHub:**
   ```bash
   git push -u origin TYP-8-database-schema
   ```
   - Go to GitHub
   - Create PR (base: `dev`, compare: `TYP-8-database-schema`)
   - Approve yourself
   - Merge

4. **Linear issue auto-closes** because commit message said "Fixes TYP-8"

---

## ML Algorithms (Week 4 Focus)

### Model A: Atomic Recommender

**Algorithm:** Ridge Regression
**Input:** user_id, place_id, companions, day_of_week, time_of_day
**Output:** predicted rating (1-10) + confidence interval

**Formula:**
```
rating = baseline + place_effect + companion_effects + day_effect + time_effect
```

**Example:**
```
You planning: Top Golf, Friday evening, with Sarah
Learned effects:
  - Baseline: 7.0
  - Top Golf: +1.2
  - Sarah: +0.5
  - Friday: +0.3
  - Evening: +0.1
Prediction: 9.1 ± 0.8
```

### Model B: Attribution Model

**Algorithm:** Hierarchical Linear Regression
**Input:** night_id (list of places in night)
**Output:** predicted night rating + per-place effects

**Why it exists:** Users only rate the night as a whole, but we need to know how much each place contributed.

**Example:**
```
Night: [Top Golf, Abe & Louie's, Trillium]
Rating: 8.5/10

Attribution:
  - Top Golf: +0.8
  - Abe & Louie's: +0.0
  - Trillium: +1.8
  - Friends vibe: -0.1
  = 8.5 ✓
```

### Why Linear, Not Deep Learning?

- **Data:** Only 400 plans (neural nets need 10k+)
- **Interpretability:** Can explain why prediction is 7.8
- **Speed:** Trains in milliseconds
- **Overfitting risk:** Lower with regularization

---

## Data Model (Week 1-3)

```sql
users(id, email, display_name, created_at)

places(id, name, lat, lng, category, source_url, google_place_id)

plans(
  id, creator_id, place_id, status, 
  scheduled_for, completed_at,
  night_id (nullable), sequence_position,
  final_rating, derived_score
)

nights(
  id, creator_id, status,
  scheduled_for, completed_at,
  final_rating, derived_score
)

comparisons(user_id, item_a_id, item_b_id, item_type, winner_id, created_at)

plan_invitations(plan_id, invitee_user_id, rsvp_status, ics_sent_at)
```

**Key design:**
- Plans are atomic (most use case)
- Nights are optional groupings (multi-stop evenings)
- Comparisons are polymorphic (works for both plans and nights)

---

## Week-by-Week Build Plan

| Week | Goal | Key Tickets |
|------|------|-------------|
| 1 | Skeleton MVP | TYP-7 (FastAPI), TYP-8 (schema), TYP-9 (endpoints), TYP-10 (iOS), TYP-11 (log flow) |
| 2 | Real data ingestion | LLM extraction, Google Places, URL paste, friend invites, map |
| 3 | Synthetic data + comparisons | Fixtures, seed script, head-to-head ranking, multi-stop nights |
| 4 | ML (centerpiece) | Atomic recommender, attribution model, eval harness, inference endpoints |
| 5 | Plan flow + calendar | Plan future flow, predictions, .ics files, email invites, RSVP, push notifications |
| 6 | Polish + demo | Tonight card, rate card, bug fixes, demo video, README, TestFlight |

---

## Important Files & Guides

**In /outputs folder:**
- `TYPE_A_SETUP_GUIDE.md` — GitHub branches, Linear integration, commit workflow
- `BRANCH_PROTECTION_SETUP.md` — How to set up branch protection
- `TYPE_A_README.md` — Project README (top-level)
- `TYPE_A_LINEAR_TICKETS.md` — All 31 tickets with estimates and dependencies
- `TYPE_A_ML_COMPLETE.md` — ML algorithms, prediction, biases, eval methodology
- `DEPENDENCIES_EXPLAINED.md` — venv, pip, requirements.txt explained simply
- `DEEP_DIVE_DEPENDENCIES.md` — Comprehensive explanation of frameworks, servers, HTTP, APIs
- `JSON_REQUEST_NITTY_GRITTY.md` — How JSON is parsed in API requests
- `TYPE_A_RATING_BIASES.md` — Known ML biases and how to address them
- `ENV_EXAMPLE.txt` — Template for .env file

---

## Local Development Setup

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15+ (Postgres.app on Mac)
- Xcode (for iOS, not needed yet)

**To run locally:**

```bash
# 1. Navigate to repo
cd ~/path/to/type-a

# 2. Activate venv
cd backend
source venv/bin/activate

# 3. Start FastAPI server
python -m uvicorn app.main:app --reload

# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Database:**
- Running on localhost:5432
- Database: `type_a_dev`
- Credentials in `.env` (not committed)

---

## Key Learnings & Insights

1. **Framework (FastAPI) is about abstraction** — lets you focus on logic, not boilerplate
2. **API requests are just HTTP** — no magic, just structured messages
3. **JSON is the bridge** — converts between Python dicts and network transmission
4. **Pydantic validates automatically** — huge time saver
5. **Uvicorn handles all network stuff** — you just write business logic
6. **Virtual environments prevent conflicts** — essential for reproducibility
7. **Branch protection enforces good habits** — PRs for everything, even solo work
8. **ML doesn't need to be complex** — linear regression works great with small data
9. **Honest about limitations** — selection bias, confounding, synthetic data are real issues
10. **Closed-loop feedback is the product** — ML is just infrastructure

---

## What's Deferred to v2

- Per-friend predicted scores (need more data)
- Auto-inferring plans from CoreLocation (2-week rabbit hole)
- Sequence-aware ML (needs real sequenced data)
- Standalone map browsing (nice-to-have)
- Calendar conflict detection (OAuth nightmare)
- Cost splitting / Venmo integration
- Reservation booking integrations
- Restaurants & food (Beli owns this)

---

## Success Metrics (Week 6)

- ✅ App on TestFlight, shareable link works
- ✅ 5+ real friends logged 5+ plans each
- ✅ Both ML models live (atomic + attribution)
- ✅ ML eval doc published with plots
- ✅ Demo video shows closed loop (save → log → rate → predict → invite)
- ✅ README good enough to substitute for behavioral interview
- ✅ Honest about limitations (selection bias, synthetic data)

---

## For New Chat: Quick Context

If starting a new chat to continue building:

1. **Current status:** TYP-7 complete (FastAPI running), ready for TYP-8 (database schema)
2. **Tech stack:** FastAPI (backend), SQLAlchemy (ORM), Postgres (DB), SwiftUI (frontend), scikit-learn (ML)
3. **Current running:** `python -m uvicorn app.main:app --reload` on localhost:8000
4. **Next task:** Create SQLAlchemy models + Alembic migrations for database schema
5. **ML approach:** Ridge regression (atomic), hierarchical regression (attribution)
6. **Key insight:** Closed-loop feedback (predict → rate → learn) is the product differentiator

---

**This project is well-scoped, technically sound, and has clear week-by-week milestones. Everything is set up correctly. Just keep building!**
