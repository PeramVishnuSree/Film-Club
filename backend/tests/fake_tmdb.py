"""An in-memory stand-in for TMDBClient used across the test suite.

It mirrors the small slice of the TMDB API surface the app actually calls
(`get_movie`, `search_movies`, `trending_movies`, `top_rated_movies`) and serves
data from a fixed catalog so tests never touch the network.
"""

from __future__ import annotations

from typing import Any

import httpx

# A handful of films with enough structure to exercise the cache layer:
# genres, keywords, credits, and region-specific watch providers.
_CATALOG: dict[int, dict[str, Any]] = {
    550: {
        "id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
        "overview": "An insomniac office worker and a soap maker form an underground club.",
        "release_date": "1999-10-15",
        "runtime": 139,
        "original_language": "en",
        "poster_path": "/fightclub.jpg",
        "backdrop_path": "/fightclub_bd.jpg",
        "popularity": 61.4,
        "vote_average": 8.4,
        "vote_count": 26000,
        "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
        "keywords": {"keywords": [{"id": 825, "name": "support group"}]},
        "credits": {
            "cast": [
                {"id": 819, "name": "Edward Norton", "character": "The Narrator", "order": 0},
                {"id": 287, "name": "Brad Pitt", "character": "Tyler Durden", "order": 1},
            ],
            "crew": [
                {"id": 7467, "name": "David Fincher", "job": "Director"},
            ],
        },
        "watch/providers": {
            "results": {
                "US": {
                    "flatrate": [
                        {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/nf.jpg"}
                    ]
                }
            }
        },
    },
    680: {
        "id": 680,
        "title": "Pulp Fiction",
        "original_title": "Pulp Fiction",
        "overview": "The lives of two mob hitmen, a boxer and others intertwine.",
        "release_date": "1994-09-10",
        "runtime": 154,
        "original_language": "en",
        "poster_path": "/pulpfiction.jpg",
        "backdrop_path": "/pulpfiction_bd.jpg",
        "popularity": 70.2,
        "vote_average": 8.5,
        "vote_count": 27000,
        "genres": [{"id": 53, "name": "Thriller"}, {"id": 80, "name": "Crime"}],
        "keywords": {"keywords": [{"id": 818, "name": "based on novel"}]},
        "credits": {
            "cast": [
                {"id": 8891, "name": "John Travolta", "character": "Vincent Vega", "order": 0},
                {"id": 139, "name": "Uma Thurman", "character": "Mia Wallace", "order": 1},
            ],
            "crew": [
                {"id": 138, "name": "Quentin Tarantino", "job": "Director"},
            ],
        },
        "watch/providers": {"results": {}},
    },
    13: {
        "id": 13,
        "title": "Forrest Gump",
        "original_title": "Forrest Gump",
        "overview": "The history of the United States through the eyes of an Alabama man.",
        "release_date": "1994-06-23",
        "runtime": 142,
        "original_language": "en",
        "poster_path": "/forrestgump.jpg",
        "backdrop_path": "/forrestgump_bd.jpg",
        "popularity": 55.1,
        "vote_average": 8.5,
        "vote_count": 25000,
        "genres": [{"id": 18, "name": "Drama"}, {"id": 35, "name": "Comedy"}],
        "keywords": {"keywords": [{"id": 422, "name": "vietnam war"}]},
        "credits": {
            "cast": [
                {"id": 31, "name": "Tom Hanks", "character": "Forrest Gump", "order": 0},
            ],
            "crew": [
                {"id": 24, "name": "Robert Zemeckis", "job": "Director"},
            ],
        },
        "watch/providers": {"results": {}},
    },
    155: {
        "id": 155,
        "title": "The Dark Knight",
        "original_title": "The Dark Knight",
        "overview": "Batman raises the stakes in his war on crime.",
        "release_date": "2008-07-16",
        "runtime": 152,
        "original_language": "en",
        "poster_path": "/darkknight.jpg",
        "backdrop_path": "/darkknight_bd.jpg",
        "popularity": 90.0,
        "vote_average": 8.5,
        "vote_count": 30000,
        "genres": [{"id": 18, "name": "Drama"}, {"id": 28, "name": "Action"}],
        "keywords": {"keywords": [{"id": 849, "name": "dc comics"}]},
        "credits": {
            "cast": [
                {"id": 3894, "name": "Christian Bale", "character": "Bruce Wayne", "order": 0},
            ],
            "crew": [
                {"id": 525, "name": "Christopher Nolan", "job": "Director"},
            ],
        },
        "watch/providers": {"results": {}},
    },
}


def _summary(detail: dict[str, Any]) -> dict[str, Any]:
    """Reduce a full detail record to the search/trending result shape."""
    keys = (
        "id",
        "title",
        "original_title",
        "overview",
        "release_date",
        "original_language",
        "poster_path",
        "backdrop_path",
        "popularity",
        "vote_average",
        "vote_count",
    )
    return {k: detail.get(k) for k in keys}


class FakeTMDB:
    """Drop-in replacement for app.services.tmdb.TMDBClient."""

    def __init__(self, catalog: dict[int, dict[str, Any]] | None = None) -> None:
        self.catalog = catalog if catalog is not None else _CATALOG

    async def aclose(self) -> None:  # pragma: no cover - nothing to close
        return None

    async def get_movie(self, tmdb_id: int) -> dict[str, Any]:
        movie = self.catalog.get(tmdb_id)
        if movie is None:
            request = httpx.Request("GET", f"https://tmdb.test/movie/{tmdb_id}")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("Not Found", request=request, response=response)
        return movie

    async def search_movies(
        self, query: str, page: int = 1, year: int | None = None
    ) -> dict[str, Any]:
        q = query.lower()
        results = []
        for detail in self.catalog.values():
            if q in detail["title"].lower():
                if year is not None:
                    rd = detail.get("release_date") or ""
                    if not rd.startswith(str(year)):
                        continue
                results.append(_summary(detail))
        return {"page": page, "results": results, "total_pages": 1, "total_results": len(results)}

    async def trending_movies(self, window: str = "week") -> dict[str, Any]:
        return {"results": [_summary(d) for d in self.catalog.values()]}

    async def top_rated_movies(self, page: int = 1) -> dict[str, Any]:
        ordered = sorted(
            self.catalog.values(), key=lambda d: d.get("vote_average", 0), reverse=True
        )
        return {"page": page, "results": [_summary(d) for d in ordered], "total_pages": 1}
