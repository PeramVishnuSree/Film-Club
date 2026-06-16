from app.schemas.film import FilmSummary


class RecommendedFilm(FilmSummary):
    """A recommended film plus a short, human-readable reason for the pick."""

    reason: str
