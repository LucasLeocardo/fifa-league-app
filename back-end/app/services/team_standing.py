"""Camada de servico da classificacao (TeamStandings)."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.repositories.cycle_season import CycleSeasonRepository
from app.repositories.team_standing import TeamStandingRepository
from app.schemas.team_standing import StandingsResponse, TeamStandingRead


class TeamStandingService:
    def __init__(
        self,
        standing_repository: TeamStandingRepository,
        cycle_season_repository: CycleSeasonRepository,
    ) -> None:
        self.standing_repository = standing_repository
        self.cycle_season_repository = cycle_season_repository

    async def get_standings(
        self, cycle_season_id: uuid.UUID | None = None
    ) -> StandingsResponse:
        """Lista a classificacao de uma CycleSeason.

        Se cycle_season_id nao for informado, usa a temporada aberta
        (CycleSeason.endDate IS NULL).
        """
        resolved_id = await self._resolve_cycle_season_id(cycle_season_id)
        rows = await self.standing_repository.list_by_cycle_season(resolved_id)
        return StandingsResponse(
            cycle_season_id=resolved_id,
            standings=[TeamStandingRead.model_validate(row) for row in rows],
        )

    async def _resolve_cycle_season_id(
        self, cycle_season_id: uuid.UUID | None
    ) -> uuid.UUID:
        if cycle_season_id is not None:
            cycle_season = await self.cycle_season_repository.get(cycle_season_id)
            if cycle_season is None:
                raise NotFoundError("CycleSeason nao encontrada.")
            return cycle_season.id

        open_cycle_season = await self.cycle_season_repository.get_open()
        if open_cycle_season is None:
            raise NotFoundError(
                "Nenhuma CycleSeason aberta encontrada (endDate vazio)."
            )
        return open_cycle_season.id
