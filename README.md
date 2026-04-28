# Type A

The social planner that learns what makes a great plan for you, then predicts how the next one will go before you commit.

## What It Is

An iOS app built around **plans** — single events with a place, a time, and people. Plans are atomic by default, but can be optionally grouped into a **night** for multi-stop evenings.

Two ML systems run in parallel:
- **Atomic recommender** — predicts how much you'll like any individual plan (place + companions + day/time)
- **Attribution model** — decomposes night ratings into per-place, per-companion contributions

Past ratings train both models. Future plans surface predicted scores in the planning UI. Plans become calendar invites.

## Demo & Links

- **TestFlight**: [Link coming in week 6]
- **Demo video**: [Link coming in week 6]
- **ML eval doc**: `/eval/README.md`

## Tech Stack

**Frontend:**
- iOS / SwiftUI
- MapKit, CoreLocation (read-only in v1)

**Backend:**
- FastAPI
- SQLAlchemy + Alembic (migrations)
- PostgreSQL

**ML:**
- scikit-learn / statsmodels (offline training)
- Jupyter notebooks for model fitting
- FastAPI inference endpoints

**Auth & Hosting:**
- Supabase or Clerk (auth)
- Fly.io or Railway (backend)
- Postgres managed (Supabase or Neon)

**Other:**
- Calendar: `.ics` file generation via Resend/SendGrid
- Place metadata: Google Places API
- Push notifications: APNs via OneSignal/Firebase

## Project Structure

```
type-a/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # Database access
│   │   └── models/            # SQLAlchemy + Pydantic
│   ├── migrations/            # Alembic migrations
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── README.md
│
├── ios/                        # SwiftUI iOS app
│   ├── TypeA.xcodeproj/
│   ├── TypeA/
│   │   ├── ContentView.swift
│   │   ├── Models/
│   │   ├── Views/
│   │   └── Networking/
│   └── README.md
│
├── eval/                       # ML evaluation & models
│   ├── README.md              # ML methodology
│   ├── notebooks/
│   │   ├── atomic_recommender.ipynb
│   │   └── attribution_model.ipynb
│   ├── plots/                 # Output evaluation plots
│   └── coefficients/          # Exported JSON for inference
│
├── fixtures/                   # Synthetic test data
│   ├── users.json
│   ├── places.json
│   ├── plans.json
│   └── seed.py                # Load fixtures into dev DB
│
├── docs/                       # Documentation
│   └── architecture.md
│
├── .gitignore
├── README.md                   # This file
└── .github/
    └── workflows/             # CI/CD (future)
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Create .env
cp .env.example .env
# Edit .env with your Postgres credentials

# Run migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`. Docs at `/docs`.

### iOS Setup

```bash
cd ios
open TypeA.xcodeproj
# Build and run in Xcode simulator (Cmd+R)
```

### ML & Evaluation

```bash
cd eval
jupyter notebook notebooks/atomic_recommender.ipynb
# Train model, export coefficients to JSON
```

## Key Design Decisions

1. **Plans are the unit. Nights are optional.** Most plans have `night_id = null`. The minority that share an evening get linked.
2. **Two-tier ML.** Atomic recommender works from day one. Attribution model kicks in once users log multi-stop nights.
3. **Closed-loop feedback.** Rating a plan makes the planner smarter. Every rating generates training data for the next prediction.
4. **Synthetic data for week 1–3.** Real data from alpha cohort validates models in week 4.

## What's Deferred to v2

- Per-friend predicted scores (not enough data by week 6)
- Auto-inferring plans from CoreLocation (2-week rabbit hole)
- Sequence-aware ML for nights (wait for more data)
- Standalone map browsing tab (Beli table-stakes, doesn't differentiate)
- Calendar conflict detection (requires OAuth per invitee)
- Cost splitting / Venmo integration
- Reservation booking (need partnerships)
- Restaurants and food (Beli owns this)

## Contributing

For now, this is a solo project. Branch strategy:
- `main` — bootstrap state
- `dev` — active development (all work here)
- `prod` — release snapshots (weekly merge from dev)

All code goes through pull requests to `dev`. See `GITHUB_SETUP_STEPS.md` for details.

## Questions?

See the scoping doc: `type_a_scoping.md`

See the setup guides:
- `GITHUB_SETUP_STEPS.md`
- `BRANCH_PROTECTION_SETUP.md`
- `TYPE_A_SETUP_GUIDE.md`