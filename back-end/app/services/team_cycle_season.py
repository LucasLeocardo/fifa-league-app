"""Camada de servico de TeamCycleSeason."""

from __future__ import annotations

import uuid

from app.repositories.team_cycle_season import TeamCycleSeasonRepository
from app.schemas.team_cycle_season import TeamCycleSeasonRead


class TeamCycleSeasonService:
    def __init__(self, repository: TeamCycleSeasonRepository) -> None:
        self.repository = repository

    async def list_current_for_user(
        self,
        user_id: uuid.UUID,
        cycle_season_id: uuid.UUID | None = None,
    ) -> list[TeamCycleSeasonRead]:
        """Lista os TeamCycleSeason de uma temporada.

        Se cycle_season_id for informado, filtra por ele. Caso contrario, usa
        a temporada atual (CycleSeason com endDate nulo). isMyTeam e true
        quando a linha pertence ao usuario do token.
        """
        rows = await self.repository.list_current(user_id, cycle_season_id)
        return [
            TeamCycleSeasonRead(
                team_cycle_season_id=row.team_cycle_season_id,
                team_name=row.team_name,
                is_my_team=row.is_my_team,
            )
            for row in rows
        ]
