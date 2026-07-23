"""Camada de servico de Match."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.repositories.match import MatchRepository
from app.schemas.match import MatchCreate, MatchRead


class MatchService:
    def __init__(self, repository: MatchRepository) -> None:
        self.repository = repository

    async def list_matches(
        self,
        user_id: uuid.UUID,
        team_cycle_season_id: uuid.UUID | None = None,
    ) -> list[MatchRead]:
        """Lista partidas de um TeamCycleSeason (mandante ou visitante).

        Se team_cycle_season_id nao for informado, resolve o TeamCycleSeason
        do usuario na temporada atual (CycleSeason.endDate IS NULL).
        """
        resolved_id = await self._resolve_team_cycle_season_id(
            user_id, team_cycle_season_id
        )
        rows = await self.repository.list_by_team_cycle_season(resolved_id)
        return [self._to_read(row) for row in rows]

    async def create_match(self, payload: MatchCreate) -> MatchRead:
        """Cria uma partida e retorna o detalhe com nomes dos times e tipo."""
        match = await self.repository.create(
            home_team_id=payload.home_team_id,
            away_team_id=payload.away_team_id,
            match_type_id=payload.match_type_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
        )
        row = await self.repository.get_detail(match.id)
        if row is None:
            raise NotFoundError("Partida criada nao encontrada.")
        return self._to_read(row)

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
                "Nenhum TeamCycleSeason encontrado para a temporada atual do usuario."
            )
        return current

    @staticmethod
    def _to_read(row) -> MatchRead:
        return MatchRead(
            match_id=row.match_id,
            home_team_name=row.home_team_name,
            away_team_name=row.away_team_name,
            home_score=row.home_score,
            away_score=row.away_score,
            match_type_name=row.match_type_name,
        )
