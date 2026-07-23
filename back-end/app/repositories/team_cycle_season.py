"""Camada de acesso a dados de TeamCycleSeason."""

import uuid
from collections.abc import Sequence

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_season import CycleSeason
from app.models.team import Team
from app.models.team_cycle_season import TeamCycleSeason

TeamCycleSeasonRow = Row[tuple[uuid.UUID, str, bool]]


class TeamCycleSeasonRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_current(
        self,
        user_id: uuid.UUID,
        cycle_season_id: uuid.UUID | None = None,
    ) -> Sequence[TeamCycleSeasonRow]:
        """Lista os TeamCycleSeason de uma temporada (todos os usuarios).

        Se cycle_season_id for informado, filtra por ele. Caso contrario, usa
        CycleSeason com endDate nulo (temporada aberta). Join com Team para
        trazer o nome do time. isMyTeam indica se a linha pertence ao user_id
        informado (obtido do token).
        """
        query = (
            select(
                TeamCycleSeason.id.label("team_cycle_season_id"),
                Team.name.label("team_name"),
                (TeamCycleSeason.user_id == user_id).label("is_my_team"),
            )
            .join(CycleSeason, CycleSeason.id == TeamCycleSeason.cycle_season_id)
            .join(Team, Team.id == TeamCycleSeason.team_id)
        )
        if cycle_season_id is not None:
            query = query.where(TeamCycleSeason.cycle_season_id == cycle_season_id)
        else:
            query = query.where(CycleSeason.end_date.is_(None))

        result = await self.db.execute(query.order_by(Team.name.asc()))
        return result.all()
