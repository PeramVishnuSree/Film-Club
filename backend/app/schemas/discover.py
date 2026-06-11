from app.schemas.film import FilmSummary


class RankedFilm(FilmSummary):
    rank: int
