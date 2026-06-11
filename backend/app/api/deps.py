from fastapi import Request

from app.services.tmdb import TMDBClient


def get_tmdb(request: Request) -> TMDBClient:
    return request.app.state.tmdb
