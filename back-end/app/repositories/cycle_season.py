"""Camada de acesso a dados de CycleSeason."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_season import CycleSeason


class CycleSeasonRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, cycle_season_id: uuid.UUID) -> CycleSeason | None:
        return await self.db.get(CycleSeason, cycle_season_id)

    async def get_open(self) -> CycleSeason | None:
        """Retorna a CycleSeason ativa (endDate nulo), a mais recente por startDate."""
        result = await self.db.execute(
            select(CycleSeason)
            .where(CycleSeason.end_date.is_(None))
            .order_by(CycleSeason.start_date.desc(), CycleSeason.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
