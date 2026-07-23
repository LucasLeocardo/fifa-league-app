"""Camada de servico do leaderboard."""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from app.core.exceptions import NotFoundError
from app.repositories.cycle_season import CycleSeasonRepository
from app.repositories.leaderboard import LeaderboardRepository
from app.schemas.leaderboard import (
    LeaderboardResponse,
    PlayerAssistsEntry,
    PlayerGoalsEntry,
    PlayerRatingEntry,
)

# Minimo de jogos do jogador em relacao ao time que mais jogou no campeonato
# para entrar na lista de notas medias.
_MIN_GAMES_RATIO = 0.75


@dataclass
class _PlayerAgg:
    player_name: str
    team_name: str
    total_goals: int = 0
    total_assists: int = 0
    rating_sum: float = 0.0
    rating_count: int = 0
    match_ids: set[uuid.UUID] = field(default_factory=set)

    @property
    def games_played(self) -> int:
        return len(self.match_ids)

    @property
    def average_rating(self) -> float | None:
        if self.rating_count == 0:
            return None
        return round(self.rating_sum / self.rating_count, 2)


class LeaderboardService:
    def __init__(
        self,
        leaderboard_repository: LeaderboardRepository,
        cycle_season_repository: CycleSeasonRepository,
    ) -> None:
        self.leaderboard_repository = leaderboard_repository
        self.cycle_season_repository = cycle_season_repository

    async def get_leaderboard(
        self,
        cycle_season_id: uuid.UUID | None = None,
        position_ids: list[uuid.UUID] | None = None,
    ) -> LeaderboardResponse:
        """Monta as 3 listas: gols, assistencias e notas (com filtro de 75%).

        position_ids vazio ou None nao filtra por posicao.
        """
        resolved_id = await self._resolve_cycle_season_id(cycle_season_id)

        matches = await self.leaderboard_repository.list_distinct_matches(
            resolved_id
        )
        match_ids = [row.match_id for row in matches]
        max_team_games = self._max_team_games(matches)
        min_games_for_rating = max_team_games * _MIN_GAMES_RATIO

        stats = await self.leaderboard_repository.list_player_stats_for_matches(
            match_ids,
            position_ids=position_ids or None,
        )
        aggregates = self._aggregate_players(stats)

        goals = sorted(
            (
                PlayerGoalsEntry(
                    player_name=agg.player_name,
                    team_name=agg.team_name,
                    total_goals=agg.total_goals,
                )
                for agg in aggregates.values()
                if agg.total_goals > 0
            ),
            key=lambda entry: (-entry.total_goals, entry.player_name),
        )
        assists = sorted(
            (
                PlayerAssistsEntry(
                    player_name=agg.player_name,
                    team_name=agg.team_name,
                    total_assists=agg.total_assists,
                )
                for agg in aggregates.values()
                if agg.total_assists > 0
            ),
            key=lambda entry: (-entry.total_assists, entry.player_name),
        )
        ratings = sorted(
            (
                PlayerRatingEntry(
                    player_name=agg.player_name,
                    team_name=agg.team_name,
                    average_rating=agg.average_rating,
                    games_played=agg.games_played,
                )
                for agg in aggregates.values()
                if agg.average_rating is not None
                and agg.games_played >= min_games_for_rating
            ),
            key=lambda entry: (-entry.average_rating, entry.player_name),
        )

        return LeaderboardResponse(
            cycle_season_id=resolved_id,
            goals=goals,
            assists=assists,
            ratings=ratings,
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

    @staticmethod
    def _max_team_games(matches: list) -> int:
        """Conta quantas partidas cada time jogou e retorna o maior valor."""
        team_games: dict[uuid.UUID, int] = defaultdict(int)
        for match in matches:
            if match.home_team_id is not None:
                team_games[match.home_team_id] += 1
            if match.away_team_id is not None:
                team_games[match.away_team_id] += 1
        return max(team_games.values()) if team_games else 0

    @staticmethod
    def _aggregate_players(stats: list) -> dict[uuid.UUID, _PlayerAgg]:
        aggregates: dict[uuid.UUID, _PlayerAgg] = {}
        for row in stats:
            agg = aggregates.get(row.player_id)
            if agg is None:
                agg = _PlayerAgg(
                    player_name=row.player_name,
                    team_name=row.team_name or "",
                )
                aggregates[row.player_id] = agg
            elif not agg.team_name and row.team_name:
                agg.team_name = row.team_name

            agg.match_ids.add(row.match_id)
            agg.total_goals += row.goals or 0
            agg.total_assists += row.assists or 0
            if row.rating is not None:
                agg.rating_sum += float(row.rating)
                agg.rating_count += 1
        return aggregates
