from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tmdb
from app.db import get_session
from app.models import User
from app.schemas.importing import ImportResult
from app.services.letterboxd import import_letterboxd_csv
from app.services.tmdb import TMDBClient

router = APIRouter(tags=["import"])

# Reject anything implausibly large before reading it into memory.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/me/import/letterboxd", response_model=ImportResult)
async def import_letterboxd(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> ImportResult:
    """Import a single Letterboxd CSV (diary, ratings, or watchlist).

    The kind is auto-detected from the header row. Films are resolved against
    TMDB by title and year; unmatched titles are returned for review.
    """
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 CSV")
    return await import_letterboxd_csv(session, tmdb, user, text)
