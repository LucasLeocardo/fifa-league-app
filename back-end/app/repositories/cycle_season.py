"""Camada de acesso a dados de CycleSeason."""

import uuid
from collections.abc import Sequence

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle import Cycle
from app.models.cycle_season import CycleSeason
from app.models.season import Season


class CycleSeasonRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, cycle_season_id: uuid.UUID) -> CycleSeason | None:
        return await self.db.get(CycleSeason, cycle_season_id)

    async def list_with_names(
        self,
    ) -> Sequence[Row[tuple[uuid.UUID, str, str, bool]]]:
        """Lista todas as CycleSeasons com o nome do ciclo e da temporada."""
        result = await self.db.execute(
            select(
                CycleSeason.id.label("cycle_season_id"),
                Cycle.name.label("cycle_name"),
                Season.name.label("season_name"),
                CycleSeason.end_date.is_(None).label("is_current_season"),
            )
            .join(Cycle, Cycle.id == CycleSeason.cycle_id)
            .join(Season, Season.id == CycleSeason.season_id)
            .order_by(CycleSeason.start_date.desc(), CycleSeason.created_at.desc())
        )
        return result.all()

    async def get_open(self) -> CycleSeason | None:
        """Retorna a CycleSeason ativa (endDate nulo), a mais recente por startDate."""
        result = await self.db.execute(
            select(CycleSeason)
            .where(CycleSeason.end_date.is_(None))
            .order_by(CycleSeason.start_date.desc(), CycleSeason.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
