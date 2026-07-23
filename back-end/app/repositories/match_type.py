"""Camada de acesso a dados de MatchType."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_type import MatchType


class MatchTypeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> Sequence[MatchType]:
        """Lista todos os MatchTypes ordenados pelo nome."""
        result = await self.db.execute(
            select(MatchType).order_by(MatchType.name.asc())
        )
        return result.scalars().all()
