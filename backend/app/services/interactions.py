from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Interaction, InteractionType


def record_interaction(
    session: AsyncSession,
    user_id: int,
    film_id: int,
    type_: InteractionType,
    value: float | None = None,
    context: dict | None = None,
) -> None:
    """Append a signal row. Caller is responsible for committing."""
    session.add(
        Interaction(
            user_id=user_id,
            film_id=film_id,
            type=type_,
            value=value,
            context=context,
        )
    )
