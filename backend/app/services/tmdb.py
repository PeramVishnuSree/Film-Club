from typing import Any

import httpx

from app.config import settings


class TMDBClient:
    """Thin async wrapper over the TMDB REST API."""

    def __init__(self) -> None:
        if settings.tmdb_access_token:
            headers = {"Authorization": f"Bearer {settings.tmdb_access_token}"}
            params = {}
        else:
            headers = {}
            params = {"api_key": settings.tmdb_api_key}
        self._client = httpx.AsyncClient(
            base_url=settings.tmdb_base_url,
            headers={"accept": "application/json", **headers},
            params=params,
            timeout=15.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_movies(self, query: str, page: int = 1) -> dict[str, Any]:
        resp = await self._client.get(
            "/search/movie",
            params={"query": query, "page": page, "include_adult": "false"},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_movie(self, tmdb_id: int) -> dict[str, Any]:
        resp = await self._client.get(
            f"/movie/{tmdb_id}",
            params={"append_to_response": "keywords,credits,watch/providers"},
        )
        resp.raise_for_status()
        return resp.json()

    async def trending_movies(self, window: str = "week") -> dict[str, Any]:
        resp = await self._client.get(f"/trending/movie/{window}")
        resp.raise_for_status()
        return resp.json()
