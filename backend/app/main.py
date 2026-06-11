from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.films import router as films_router
from app.api.health import router as health_router
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
app.include_router(films_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
