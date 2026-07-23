"""Camada de acesso a dados do leaderboard."""

import uuid
from collections.abc import Sequence

from sqlalchemy import Row, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.match_player_stat import MatchPlayerStat
from app.models.player import Player
from app.models.player_position import PlayerPosition
from app.models.team import Team
from app.models.team_cycle_season import TeamCycleSeason
from app.models.team_squad import TeamSquad

MatchRow = Row[tuple[uuid.UUID, uuid.UUID | None, uuid.UUID | None]]
PlayerStatRow = Row[
    tuple[uuid.UUID, uuid.UUID, str, str, int | None, int | None, float | None]
]


class LeaderboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_distinct_matches(
        self, cycle_season_id: uuid.UUID
    ) -> Sequence[MatchRow]:
        """Lista partidas distintas da CycleSeason.

        Parte de TeamCycleSeason filtrado pelo cycleSeasonId e faz join com
        Match por homeTeamId OU awayTeamId. Retorna matchId, homeTeamId e
        awayTeamId sem duplicatas de partida.
        """
        result = await self.db.execute(
            select(
                Match.id.label("match_id"),
                Match.home_team_id.label("home_team_id"),
                Match.away_team_id.label("away_team_id"),
            )
            .select_from(TeamCycleSeason)
            .join(
                Match,
                or_(
                    Match.home_team_id == TeamCycleSeason.id,
                    Match.away_team_id == TeamCycleSeason.id,
                ),
            )
            .where(TeamCycleSeason.cycle_season_id == cycle_season_id)
            .distinct()
        )
        return result.all()

    async def list_player_stats_for_matches(
        self,
        match_ids: Sequence[uuid.UUID],
        position_ids: Sequence[uuid.UUID] | None = None,
    ) -> Sequence[PlayerStatRow]:
        """Stats de jogadores nas partidas informadas.

        Join em TeamSquad -> TeamCycleSeason -> Team para o nome do time, e
        em Player para o nome do jogador. Se position_ids for informado e nao
        vazio, restringe aos jogadores que possuem ao menos uma dessas
        posicoes em PlayerPosition.
        """
        if not match_ids:
            return []

        query = (
            select(
                MatchPlayerStat.match_id.label("match_id"),
                MatchPlayerStat.player_id.label("player_id"),
                Player.name.label("player_name"),
                func.coalesce(Team.name, "").label("team_name"),
                MatchPlayerStat.goals.label("goals"),
                MatchPlayerStat.assists.label("assists"),
                MatchPlayerStat.rating.label("rating"),
            )
            .select_from(MatchPlayerStat)
            .join(Player, Player.id == MatchPlayerStat.player_id)
            .outerjoin(TeamSquad, TeamSquad.id == MatchPlayerStat.team_squad_id)
            .outerjoin(
                TeamCycleSeason,
                TeamCycleSeason.id == TeamSquad.team_cycle_season_id,
            )
            .outerjoin(Team, Team.id == TeamCycleSeason.team_id)
            .where(MatchPlayerStat.match_id.in_(match_ids))
        )

        if position_ids:
            query = query.where(
                MatchPlayerStat.player_id.in_(
                    select(PlayerPosition.player_id).where(
                        PlayerPosition.position_id.in_(position_ids)
                    )
                )
            )

        result = await self.db.execute(query)
        return result.all()
