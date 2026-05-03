from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import places as places_routes
from app.routes import users as users_routes
from app.routes import events as events_routes
from app.routes import outings as outings_routes
from app.routes import place_ratings as place_ratings_routes
from app.routes import friendships as friendships_routes
from app.routes import feed as feed_routes

app = FastAPI(
    title="Type A API",
    description="Social planner with ML predictions",
    version="0.1.0",
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to Type A API"}
