from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ml.atomic_recommender import get_model
from app.routes import places as places_routes
from app.routes import users as users_routes
from app.routes import events as events_routes
from app.routes import outings as outings_routes
from app.routes import place_ratings as place_ratings_routes
from app.routes import friendships as friendships_routes
from app.routes import feed as feed_routes
from app.routes import event_invitations as event_invitations_routes
from app.routes import outing_invitations as outing_invitations_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown work. Everything before `yield` runs once at boot."""
    # Load the Atomic Recommender before accepting traffic. A missing or
    # version-stale artifact raises here, which fails the deploy outright and
    # leaves the previous version live on Render. The alternative — finding out
    # on the first user's request — means a green deploy quietly serving wrong
    # numbers, which is what load_json's version gate exists to prevent.
    # Nothing to tear down, so there's no code after the yield.
    get_model()
    yield


app = FastAPI(
    title="Type A API",
    description="Social planner with ML predictions",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_routes.router)
app.include_router(places_routes.router)
app.include_router(events_routes.router)
app.include_router(outings_routes.router)
app.include_router(place_ratings_routes.router)
app.include_router(friendships_routes.router)
app.include_router(feed_routes.router)
app.include_router(event_invitations_routes.router)
app.include_router(outing_invitations_routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to Type A API"}
