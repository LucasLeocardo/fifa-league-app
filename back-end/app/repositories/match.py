"""Camada de acesso a dados de Match."""

import uuid
from collections.abc import Sequence

from sqlalchemy import Row, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.cycle_season import CycleSeason
from app.models.match import Match
from app.models.match_type import MatchType
from app.models.team import Team
from app.models.team_cycle_season import TeamCycleSeason

MatchRow = Row[
    tuple[uuid.UUID, str, str, int | None, int | None, str | None]
]


class MatchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_current_team_cycle_season_id(
        self, user_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Resolve o TeamCycleSeason do usuario na temporada atual.

        Join com CycleSeason filtrando endDate nulo (temporada aberta).
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

    async def list_by_team_cycle_season(
        self, team_cycle_season_id: uuid.UUID
    ) -> Sequence[MatchRow]:
        """Lista partidas em que o TeamCycleSeason e mandante ou visitante.

        Inclui placar, nome dos dois times e nome do MatchType.
        """
        home_tcs = aliased(TeamCycleSeason)
        away_tcs = aliased(TeamCycleSeason)
        home_team = aliased(Team)
        away_team = aliased(Team)

        result = await self.db.execute(
            select(
                Match.id.label("match_id"),
                func.coalesce(home_team.name, "").label("home_team_name"),
                func.coalesce(away_team.name, "").label("away_team_name"),
                Match.home_score.label("home_score"),
                Match.away_score.label("away_score"),
                MatchType.name.label("match_type_name"),
            )
            .select_from(Match)
            .outerjoin(home_tcs, home_tcs.id == Match.home_team_id)
            .outerjoin(home_team, home_team.id == home_tcs.team_id)
            .outerjoin(away_tcs, away_tcs.id == Match.away_team_id)
            .outerjoin(away_team, away_team.id == away_tcs.team_id)
            .outerjoin(MatchType, MatchType.id == Match.type_id)
            .where(
                or_(
                    Match.home_team_id == team_cycle_season_id,
                    Match.away_team_id == team_cycle_season_id,
                )
            )
            .order_by(Match.created_at.asc(), Match.id.asc())
        )
        return result.all()

    async def get_detail(self, match_id: uuid.UUID) -> MatchRow | None:
        """Retorna uma partida com nomes dos times e do MatchType."""
        home_tcs = aliased(TeamCycleSeason)
        away_tcs = aliased(TeamCycleSeason)
        home_team = aliased(Team)
        away_team = aliased(Team)

        result = await self.db.execute(
            select(
                Match.id.label("match_id"),
                func.coalesce(home_team.name, "").label("home_team_name"),
                func.coalesce(away_team.name, "").label("away_team_name"),
                Match.home_score.label("home_score"),
                Match.away_score.label("away_score"),
                MatchType.name.label("match_type_name"),
            )
            .select_from(Match)
            .outerjoin(home_tcs, home_tcs.id == Match.home_team_id)
            .outerjoin(home_team, home_team.id == home_tcs.team_id)
            .outerjoin(away_tcs, away_tcs.id == Match.away_team_id)
            .outerjoin(away_team, away_team.id == away_tcs.team_id)
            .outerjoin(MatchType, MatchType.id == Match.type_id)
            .where(Match.id == match_id)
        )
        return result.one_or_none()

    async def create(
        self,
        home_team_id: uuid.UUID,
        away_team_id: uuid.UUID,
        match_type_id: uuid.UUID,
        home_score: int,
        away_score: int,
    ) -> Match:
        """Insere uma nova linha em Match e retorna a entidade persistida."""
        match = Match(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            type_id=match_type_id,
            home_score=home_score,
            away_score=away_score,
        )
        self.db.add(match)
        await self.db.commit()
        await self.db.refresh(match)
        return match
