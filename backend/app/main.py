from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.discover import router as discover_router
from app.api.films import router as films_router
from app.api.health import router as health_router
from app.api.library import router as library_router
from app.api.social import router as social_router
from app.config import settings
from app.services.tmdb import TMDBClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.tmdb = TMDBClient()
    try:
        yield
    finally:
        await app.state.tmdb.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(discover_router)
app.include_router(films_router)
app.include_router(library_router)
app.include_router(social_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
