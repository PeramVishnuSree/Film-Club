import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user, get_tmdb
from app.db import get_session
from app.models import (
    Film,
    InteractionType,
    List,
    ListItem,
    ListLike,
    NotificationType,
    User,
)
from app.schemas.lists import (
    ListCreate,
    ListDetail,
    ListFilm,
    ListItemIn,
    ListItemNote,
    ListItemOut,
    ListReorder,
    ListSummary,
    ListUpdate,
)
from app.schemas.social import UserCard
from app.services.film_cache import get_or_cache_film
from app.services.interactions import record_interaction
from app.services.notifications import notify
from app.services.tmdb import TMDBClient

router = APIRouter(tags=["lists"])

PREVIEW_COUNT = 5


# ------------------------------------------------------------------ helpers


def _film_to_listfilm(film: Film) -> ListFilm:
    return ListFilm(
        tmdb_id=film.tmdb_id,
        title=film.title,
        release_date=film.release_date.isoformat() if film.release_date else None,
        poster_path=film.poster_path,
        vote_average=film.vote_average,
    )


async def _list_meta(
    session: AsyncSession, lst: List, owner: User | None
) -> tuple[int, list[str]]:
    """Item count and the first few poster paths for a preview strip."""
    count = (
        await session.execute(
            select(func.count(ListItem.id)).where(ListItem.list_id == lst.id)
        )
    ).scalar_one()
    order = ListItem.rank.asc().nulls_last() if lst.is_ranked else ListItem.id.asc()
    posters = (
        await session.execute(
            select(Film.poster_path)
            .join(ListItem, ListItem.film_id == Film.id)
            .where(ListItem.list_id == lst.id, Film.poster_path.isnot(None))
            .order_by(order)
            .limit(PREVIEW_COUNT)
        )
    ).scalars().all()
    return count, list(posters)


async def _like_meta(
    session: AsyncSession, lst: List, viewer: User | None
) -> tuple[int, bool]:
    """Total likes on a list and whether the viewer is one of them."""
    count = (
        await session.execute(
            select(func.count()).select_from(ListLike).where(ListLike.list_id == lst.id)
        )
    ).scalar_one()
    liked = False
    if viewer is not None:
        liked = (
            await session.execute(
                select(ListLike.id).where(
                    ListLike.list_id == lst.id, ListLike.user_id == viewer.id
                )
            )
        ).first() is not None
    return count, liked


async def _summary(
    session: AsyncSession, lst: List, owner: User | None, viewer: User | None = None
) -> ListSummary:
    count, posters = await _list_meta(session, lst, owner)
    like_count, liked = await _like_meta(session, lst, viewer)
    return ListSummary(
        id=lst.id,
        title=lst.title,
        description=lst.description,
        is_ranked=lst.is_ranked,
        is_public=lst.is_public,
        is_system=lst.is_system,
        item_count=count,
        owner=UserCard.model_validate(owner) if owner else None,
        created_at=lst.created_at,
        preview_posters=posters,
        like_count=like_count,
        liked=liked,
    )


async def _detail(
    session: AsyncSession, lst: List, owner: User | None, viewer: User | None
) -> ListDetail:
    order = ListItem.rank.asc().nulls_last() if lst.is_ranked else ListItem.id.asc()
    rows = (
        await session.execute(
            select(ListItem, Film)
            .join(Film, Film.id == ListItem.film_id)
            .where(ListItem.list_id == lst.id)
            .order_by(order)
        )
    ).all()
    items = [
        ListItemOut(film=_film_to_listfilm(film), rank=item.rank, note=item.note)
        for item, film in rows
    ]
    posters = [f.film.poster_path for f in items if f.film.poster_path][:PREVIEW_COUNT]
    like_count, liked = await _like_meta(session, lst, viewer)
    return ListDetail(
        id=lst.id,
        title=lst.title,
        description=lst.description,
        is_ranked=lst.is_ranked,
        is_public=lst.is_public,
        is_system=lst.is_system,
        item_count=len(items),
        owner=UserCard.model_validate(owner) if owner else None,
        created_at=lst.created_at,
        preview_posters=posters,
        items=items,
        is_owner=viewer is not None and owner is not None and viewer.id == owner.id,
        like_count=like_count,
        liked=liked,
    )


async def _get_owned_list(session: AsyncSession, list_id: int, user: User) -> List:
    lst = await session.get(List, list_id)
    if lst is None:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.is_system or lst.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your list")
    return lst


async def _resolve_film(
    session: AsyncSession, tmdb: TMDBClient, tmdb_id: int, region: str
) -> Film:
    try:
        return await get_or_cache_film(session, tmdb, tmdb_id, region)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Film not found on TMDB") from exc
        raise HTTPException(status_code=502, detail="TMDB request failed") from exc


async def _next_rank(session: AsyncSession, list_id: int) -> int:
    current = (
        await session.execute(
            select(func.max(ListItem.rank)).where(ListItem.list_id == list_id)
        )
    ).scalar_one()
    return (current or 0) + 1


# ------------------------------------------------------------------ CRUD


@router.post("/lists", response_model=ListDetail, status_code=status.HTTP_201_CREATED)
async def create_list(
    payload: ListCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ListDetail:
    lst = List(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        is_ranked=payload.is_ranked,
        is_public=payload.is_public,
        is_system=False,
    )
    session.add(lst)
    await session.commit()
    await session.refresh(lst)
    return await _detail(session, lst, user, user)


@router.get("/lists/{list_id}", response_model=ListDetail)
async def get_list(
    list_id: int,
    session: AsyncSession = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
) -> ListDetail:
    lst = await session.get(List, list_id)
    if lst is None:
        raise HTTPException(status_code=404, detail="List not found")
    owner = await session.get(User, lst.user_id) if lst.user_id else None
    is_owner = viewer is not None and owner is not None and viewer.id == owner.id
    if not lst.is_public and not lst.is_system and not is_owner:
        # Don't reveal existence of someone else's private list.
        raise HTTPException(status_code=404, detail="List not found")
    return await _detail(session, lst, owner, viewer)


@router.patch("/lists/{list_id}", response_model=ListDetail)
async def update_list(
    list_id: int,
    payload: ListUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ListDetail:
    lst = await _get_owned_list(session, list_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lst, field, value)
    await session.commit()
    await session.refresh(lst)
    return await _detail(session, lst, user, user)


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    lst = await _get_owned_list(session, list_id, user)
    await session.delete(lst)  # cascade drops list_items
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ items


@router.post(
    "/lists/{list_id}/items", response_model=ListItemOut, status_code=status.HTTP_201_CREATED
)
async def add_item(
    list_id: int,
    payload: ListItemIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> ListItemOut:
    lst = await _get_owned_list(session, list_id, user)
    film = await _resolve_film(session, tmdb, payload.tmdb_id, user.region)
    existing = (
        await session.execute(
            select(ListItem).where(
                ListItem.list_id == lst.id, ListItem.film_id == film.id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Film already in this list")
    rank = await _next_rank(session, lst.id) if lst.is_ranked else None
    item = ListItem(list_id=lst.id, film_id=film.id, rank=rank, note=payload.note)
    session.add(item)
    record_interaction(
        session, user.id, film.id, InteractionType.list_add, context={"list_id": lst.id}
    )
    await session.commit()
    return ListItemOut(film=_film_to_listfilm(film), rank=rank, note=payload.note)


@router.patch("/lists/{list_id}/items/{tmdb_id}", response_model=ListItemOut)
async def update_item_note(
    list_id: int,
    tmdb_id: int,
    payload: ListItemNote,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ListItemOut:
    lst = await _get_owned_list(session, list_id, user)
    row = (
        await session.execute(
            select(ListItem, Film)
            .join(Film, Film.id == ListItem.film_id)
            .where(ListItem.list_id == lst.id, Film.tmdb_id == tmdb_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Film not in this list")
    item, film = row
    item.note = payload.note
    await session.commit()
    return ListItemOut(film=_film_to_listfilm(film), rank=item.rank, note=item.note)


@router.delete(
    "/lists/{list_id}/items/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_item(
    list_id: int,
    tmdb_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    lst = await _get_owned_list(session, list_id, user)
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if film is not None:
        item = (
            await session.execute(
                select(ListItem).where(
                    ListItem.list_id == lst.id, ListItem.film_id == film.id
                )
            )
        ).scalar_one_or_none()
        if item is not None:
            await session.delete(item)
            await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/lists/{list_id}/order", response_model=ListDetail)
async def reorder_list(
    list_id: int,
    payload: ListReorder,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ListDetail:
    lst = await _get_owned_list(session, list_id, user)
    if not lst.is_ranked:
        raise HTTPException(status_code=400, detail="List is not ranked")
    rows = (
        await session.execute(
            select(ListItem, Film.tmdb_id)
            .join(Film, Film.id == ListItem.film_id)
            .where(ListItem.list_id == lst.id)
        )
    ).all()
    by_tmdb = {tmdb_id: item for item, tmdb_id in rows}
    # Apply the requested order first; any items omitted keep their relative
    # order after, so a partial reorder can't drop films.
    rank = 0
    seen: set[int] = set()
    for tmdb_id in payload.tmdb_ids:
        item = by_tmdb.get(tmdb_id)
        if item is not None and tmdb_id not in seen:
            rank += 1
            item.rank = rank
            seen.add(tmdb_id)
    for item, tmdb_id in rows:
        if tmdb_id not in seen:
            rank += 1
            item.rank = rank
    await session.commit()
    await session.refresh(lst)
    return await _detail(session, lst, user, user)


# ------------------------------------------------------------------ likes


@router.post("/lists/{list_id}/like", status_code=status.HTTP_201_CREATED)
async def like_list(
    list_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | int]:
    lst = await session.get(List, list_id)
    if lst is None:
        raise HTTPException(status_code=404, detail="List not found")
    if not lst.is_public and not lst.is_system and lst.user_id != user.id:
        raise HTTPException(status_code=404, detail="List not found")
    existing = (
        await session.execute(
            select(ListLike).where(
                ListLike.user_id == user.id, ListLike.list_id == list_id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(ListLike(user_id=user.id, list_id=list_id))
        if lst.user_id is not None:
            notify(
                session,
                user_id=lst.user_id,
                actor_id=user.id,
                type_=NotificationType.list_like,
                data={"list_id": lst.id, "list_title": lst.title},
            )
        await session.commit()
    count = (
        await session.execute(
            select(func.count()).select_from(ListLike).where(ListLike.list_id == list_id)
        )
    ).scalar_one()
    return {"liked": True, "like_count": count}


@router.delete("/lists/{list_id}/like", status_code=status.HTTP_200_OK)
async def unlike_list(
    list_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | int]:
    await session.execute(
        delete(ListLike).where(
            ListLike.user_id == user.id, ListLike.list_id == list_id
        )
    )
    await session.commit()
    count = (
        await session.execute(
            select(func.count()).select_from(ListLike).where(ListLike.list_id == list_id)
        )
    ).scalar_one()
    return {"liked": False, "like_count": count}


# ------------------------------------------------------------------ collections


@router.get("/me/lists", response_model=list[ListSummary])
async def my_lists(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ListSummary]:
    lists = (
        await session.execute(
            select(List)
            .where(List.user_id == user.id)
            .order_by(List.id.desc())
        )
    ).scalars().all()
    return [await _summary(session, lst, user, user) for lst in lists]


@router.get("/users/{username}/lists", response_model=list[ListSummary])
async def user_lists(
    username: str,
    session: AsyncSession = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ListSummary]:
    owner = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="User not found")
    is_owner = viewer is not None and viewer.id == owner.id
    query = select(List).where(List.user_id == owner.id)
    if not is_owner:
        query = query.where(List.is_public.is_(True))
    lists = (
        await session.execute(
            query.order_by(List.id.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return [await _summary(session, lst, owner, viewer) for lst in lists]
