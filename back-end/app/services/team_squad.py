"""Camada de servico do elenco (TeamSquad)."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.repositories.team_squad import TeamSquadRepository
from app.schemas.team_squad import (
    SquadPlayerRead,
    SquadResponse,
    TeamSquadEntryRead,
)


class TeamSquadService:
    def __init__(self, repository: TeamSquadRepository) -> None:
        self.repository = repository

    async def get_squad(
        self,
        user_id: uuid.UUID,
        team_cycle_season_id: uuid.UUID | None = None,
    ) -> SquadResponse:
        """Lista o elenco de um TeamCycleSeason.

        Se team_cycle_season_id nao for informado, resolve o TeamCycleSeason do
        usuario (do token) na temporada atual (CycleSeason.endDate IS NULL).
        """
        resolved_id = await self._resolve_team_cycle_season_id(
            user_id, team_cycle_season_id
        )
        rows = await self.repository.list_squad(resolved_id)
        players = [
            SquadPlayerRead(
                team_squad_id=row.team_squad_id,
                player_name=row.player_name,
                overall=row.overall,
                player_cost=row.player_cost,
                currency=row.currency,
                shirt_number=row.shirt_number,
                positions=list(row.positions or []),
                total_goals=row.total_goals,
                total_assists=row.total_assists,
                average_rating=(
                    round(row.average_rating, 2)
                    if row.average_rating is not None
                    else None
                ),
            )
            for row in rows
        ]
        return SquadResponse(team_cycle_season_id=resolved_id, players=players)

    async def update_shirt_number(
        self, team_squad_id: uuid.UUID, shirt_number: int
    ) -> TeamSquadEntryRead:
        """Atualiza o numero da camisa de uma linha de TeamSquad."""
        squad = await self.repository.update_shirt_number(
            team_squad_id, shirt_number
        )
        if squad is None:
            raise NotFoundError("TeamSquad nao encontrado.")
        return TeamSquadEntryRead(
            team_squad_id=squad.id,
            shirt_number=squad.shirt_number,
        )

    async def _resolve_team_cycle_season_id(
        self,
        user_id: uuid.UUID,
        team_cycle_season_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if team_cycle_season_id is not None:
            return team_cycle_season_id

        current = await self.repository.get_current_team_cycle_season_id(user_id)
        if current is None:
            raise NotFoundError(
                "Nenhum elenco encontrado para a temporada atual do usuario."
            )
        return current
