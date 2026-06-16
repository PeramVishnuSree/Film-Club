from pydantic import BaseModel


class ImportResult(BaseModel):
    kind: str  # diary | ratings | watchlist
    rows: int  # data rows seen in the file
    imported: int  # records created
    skipped: int  # rows already present / duplicates
    unmatched: list[str]  # film titles we couldn't resolve on TMDB
