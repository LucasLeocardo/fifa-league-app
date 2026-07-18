"""Camada de acesso a dados da view TeamStandings."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_standing import TeamStanding


class TeamStandingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_cycle_season(
        self, cycle_season_id: uuid.UUID
    ) -> Sequence[TeamStanding]:
        result = await self.db.execute(
            select(TeamStanding)
            .where(TeamStanding.cycle_season_id == cycle_season_id)
            .order_by(
                TeamStanding.points.desc(),
                TeamStanding.wins.desc(),
                TeamStanding.goal_difference.desc(),
                TeamStanding.goals_for.desc(),
                TeamStanding.team_name.asc(),
            )
        )
        return result.scalars().all()
