import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.discover import router as discover_router
from app.api.films import router as films_router
from app.api.health import router as health_router
from app.api.importing import router as importing_router
from app.api.library import router as library_router
from app.api.lists import router as lists_router
from app.api.notifications import router as notifications_router
from app.api.social import router as social_router
from app.config import settings
from app.services.tmdb import TMDBClient
from app.services.top500 import seed_top_500_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuse to boot with insecure config (e.g. default SECRET_KEY) in production.
    settings.validate_for_production()
    app.state.tmdb = TMDBClient()
    # Populate the Top 500 on a fresh database, in the background so it never
    # blocks startup or the platform health check. No-ops once it has items.
    seed_task = asyncio.create_task(seed_top_500_if_empty(app.state.tmdb))
    try:
        yield
    finally:
        # Stop the seed cleanly before closing the shared TMDB client it uses.
        if not seed_task.done():
            seed_task.cancel()
            try:
                await seed_task
            except asyncio.CancelledError:
                pass
        await app.state.tmdb.aclose()


# Hide interactive API docs / schema in production to avoid leaking the full
# surface to anonymous visitors. They stay on in development.
_docs_kwargs = (
    {"docs_url": None, "redoc_url": None, "openapi_url": None}
    if settings.is_production
    else {}
)

app = FastAPI(title=settings.app_name, lifespan=lifespan, **_docs_kwargs)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Conservative hardening headers on every response. HSTS is only emitted
    in production, where the app is expected to be served over HTTPS."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    return response


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
app.include_router(lists_router)
app.include_router(social_router)
app.include_router(notifications_router)
app.include_router(importing_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
