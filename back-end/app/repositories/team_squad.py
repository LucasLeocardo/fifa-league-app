"""Camada de acesso a dados do elenco (TeamSquad)."""

import uuid
from collections.abc import Sequence

from sqlalchemy import Row, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_season import CycleSeason
from app.models.match_player_stat import MatchPlayerStat
from app.models.overall import Overall
from app.models.player import Player
from app.models.player_position import PlayerPosition
from app.models.position import Position
from app.models.team_cycle_season import TeamCycleSeason
from app.models.team_squad import TeamSquad

SquadRow = Row[
    tuple[
        uuid.UUID,
        str,
        int | None,
        int | None,
        str | None,
        int | None,
        list[str],
        int,
        int,
        float | None,
    ]
]


class TeamSquadRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def update_shirt_number(
        self, team_squad_id: uuid.UUID, shirt_number: int
    ) -> TeamSquad | None:
        """Atualiza o numero da camisa de uma linha de TeamSquad.

        Retorna a linha atualizada ou None se o id nao existir.
        """
        squad = await self.db.get(TeamSquad, team_squad_id)
        if squad is None:
            return None
        squad.shirt_number = shirt_number
        await self.db.commit()
        await self.db.refresh(squad)
        return squad

    async def get_current_team_cycle_season_id(
        self, user_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Resolve o TeamCycleSeason do usuario na temporada atual.

        Faz join com CycleSeason e filtra endDate nulo (temporada aberta),
        retornando o id do TeamCycleSeason correspondente.
        """
        result = await self.db.execute(
            select(TeamCycleSeason.id)
            .join(CycleSeason, CycleSeason.id == TeamCycleSeason.cycle_season_id)
            .where(TeamCycleSeason.user_id == user_id)
            .where(CycleSeason.end_date.is_(None))
            .order_by(
                CycleSeason.start_date.desc(),
                TeamCycleSeason.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_squad(
        self, team_cycle_season_id: uuid.UUID
    ) -> Sequence[SquadRow]:
        """Lista os jogadores do elenco com nome, overall, numero da camisa,
        posicoes (array), o id da linha em TeamSquad e as estatisticas agregadas
        de MatchPlayerStat: total de gols, total de assistencias e media das
        notas (por teamSquadId)."""
        positions = func.array_remove(
            func.array_agg(distinct(Position.code)), None
        ).label("positions")

        # Estatisticas por teamSquadId em subquery, para nao serem infladas pelo
        # join de posicoes (que multiplica linhas por jogador).
        stats = (
            select(
                MatchPlayerStat.team_squad_id.label("team_squad_id"),
                func.coalesce(func.sum(MatchPlayerStat.goals), 0).label(
                    "total_goals"
                ),
                func.coalesce(func.sum(MatchPlayerStat.assists), 0).label(
                    "total_assists"
                ),
                func.avg(MatchPlayerStat.rating).label("average_rating"),
            )
            .where(MatchPlayerStat.team_squad_id.is_not(None))
            .group_by(MatchPlayerStat.team_squad_id)
            .subquery()
        )

        result = await self.db.execute(
            select(
                TeamSquad.id.label("team_squad_id"),
                Player.name.label("player_name"),
                Overall.value.label("overall"),
                Overall.player_cost.label("player_cost"),
                Overall.currency.label("currency"),
                TeamSquad.shirt_number.label("shirt_number"),
                positions,
                func.coalesce(stats.c.total_goals, 0).label("total_goals"),
                func.coalesce(stats.c.total_assists, 0).label("total_assists"),
                stats.c.average_rating.label("average_rating"),
            )
            .select_from(TeamSquad)
            .join(Player, Player.id == TeamSquad.player_id)
            .outerjoin(Overall, Overall.id == Player.overall_id)
            .outerjoin(PlayerPosition, PlayerPosition.player_id == Player.id)
            .outerjoin(Position, Position.id == PlayerPosition.position_id)
            .outerjoin(stats, stats.c.team_squad_id == TeamSquad.id)
            .where(TeamSquad.team_cycle_season_id == team_cycle_season_id)
            .group_by(
                TeamSquad.id,
                Player.name,
                Overall.value,
                Overall.player_cost,
                Overall.currency,
                TeamSquad.shirt_number,
                stats.c.total_goals,
                stats.c.total_assists,
                stats.c.average_rating,
            )
            .order_by(
                TeamSquad.shirt_number.asc().nulls_last(),
                Player.name.asc(),
            )
        )
        return result.all()
