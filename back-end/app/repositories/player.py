"""Camada de acesso a dados de Player."""

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import Row, delete, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_season import CycleSeason
from app.models.match_player_stat import MatchPlayerStat
from app.models.overall import Overall
from app.models.player import Player
from app.models.player_position import PlayerPosition
from app.models.position import Position
from app.models.team import Team
from app.models.team_cycle_season import TeamCycleSeason
from app.models.team_squad import TeamSquad

PlayerSearchRow = Row[
    tuple[
        uuid.UUID,
        str,
        int | None,
        list[str],
        list[uuid.UUID],
        str | None,
        uuid.UUID | None,
    ]
]


class PlayerRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _search_select(self):
        """Select base da busca/detalhe de jogador."""
        positions = func.array_remove(
            func.array_agg(distinct(Position.code)), None
        ).label("positions")
        position_ids = func.array_remove(
            func.array_agg(distinct(Position.id)), None
        ).label("position_ids")

        current_team = (
            select(
                TeamSquad.player_id.label("player_id"),
                Team.name.label("team_name"),
                TeamCycleSeason.id.label("team_cycle_season_id"),
            )
            .distinct(TeamSquad.player_id)
            .select_from(TeamSquad)
            .join(
                TeamCycleSeason,
                TeamCycleSeason.id == TeamSquad.team_cycle_season_id,
            )
            .join(
                CycleSeason,
                CycleSeason.id == TeamCycleSeason.cycle_season_id,
            )
            .join(Team, Team.id == TeamCycleSeason.team_id)
            .where(CycleSeason.end_date.is_(None))
            .order_by(TeamSquad.player_id, TeamSquad.created_at.desc())
            .subquery("current_team")
        )

        return (
            select(
                Player.id.label("player_id"),
                Player.name.label("player_name"),
                Overall.value.label("overall"),
                positions,
                position_ids,
                current_team.c.team_name.label("team_name"),
                current_team.c.team_cycle_season_id.label(
                    "team_cycle_season_id"
                ),
            )
            .select_from(Player)
            .join(Overall, Overall.id == Player.overall_id, isouter=True)
            .join(
                PlayerPosition,
                PlayerPosition.player_id == Player.id,
                isouter=True,
            )
            .join(
                Position,
                Position.id == PlayerPosition.position_id,
                isouter=True,
            )
            .join(
                current_team,
                current_team.c.player_id == Player.id,
                isouter=True,
            )
            .group_by(
                Player.id,
                Player.name,
                Overall.value,
                current_team.c.team_name,
                current_team.c.team_cycle_season_id,
            )
        )

    async def search_by_name(self, name: str) -> Sequence[PlayerSearchRow]:
        """Busca jogadores cujo name contains o texto informado (ILIKE).

        Inclui overall, posicoes (codes e ids) e o time da temporada atual
        (CycleSeason com endDate nulo), quando existir. Jogadores sem time
        na temporada atual tambem entram no resultado (LEFT JOIN).
        """
        result = await self.db.execute(
            self._search_select()
            .where(Player.name.ilike(f"%{name}%"))
            .order_by(Player.name.asc())
        )
        return result.all()

    async def get_detail(self, player_id: uuid.UUID) -> PlayerSearchRow | None:
        """Detalhe de um jogador no mesmo formato da busca."""
        result = await self.db.execute(
            self._search_select().where(Player.id == player_id)
        )
        return result.one_or_none()

    async def get_by_id(self, player_id: uuid.UUID) -> Player | None:
        """Busca Player pelo id."""
        return await self.db.get(Player, player_id)

    async def list_squad_players_by_team_cycle_season(
        self, team_cycle_season_id: uuid.UUID
    ) -> Sequence[tuple[uuid.UUID, str, uuid.UUID]]:
        """Jogadores do elenco: (player_id, player_name, team_squad_id)."""
        result = await self.db.execute(
            select(Player.id, Player.name, TeamSquad.id)
            .select_from(TeamSquad)
            .join(Player, Player.id == TeamSquad.player_id)
            .where(TeamSquad.team_cycle_season_id == team_cycle_season_id)
            .order_by(Player.name.asc())
        )
        return result.all()

    async def list_name_candidates(
        self, name: str, *, limit: int = 40
    ) -> Sequence[tuple[uuid.UUID, str]]:
        """Candidatos globais por trechos do nome (para fallback do matching)."""
        tokens = [t for t in name.strip().split() if len(t) >= 2]
        if not tokens:
            tokens = [name.strip()] if name.strip() else []
        if not tokens:
            return []

        stmt = select(Player.id, Player.name)
        # Prefere candidatos que casam com o maior token (sobrenome costuma ser maior).
        primary = max(tokens, key=len)
        stmt = stmt.where(Player.name.ilike(f"%{primary}%"))
        stmt = stmt.order_by(Player.name.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return result.all()

    async def get_team_squad_id(
        self, *, team_cycle_season_id: uuid.UUID, player_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Resolve TeamSquad.id pelo time da temporada + jogador."""
        result = await self.db.execute(
            select(TeamSquad.id)
            .where(TeamSquad.team_cycle_season_id == team_cycle_season_id)
            .where(TeamSquad.player_id == player_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_overall_by_value(self, value: int) -> Overall | None:
        """Busca a linha de Overall pelo value (nota)."""
        result = await self.db.execute(
            select(Overall).where(Overall.value == value).limit(1)
        )
        return result.scalar_one_or_none()

    async def exists_by_name(
        self, name: str, exclude_player_id: uuid.UUID | None = None
    ) -> bool:
        """Indica se ja existe um Player com esse nome (case-insensitive)."""
        stmt = select(Player.id).where(func.lower(Player.name) == name.lower())
        if exclude_player_id is not None:
            stmt = stmt.where(Player.id != exclude_player_id)
        result = await self.db.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def list_position_codes_by_ids(
        self, position_ids: Sequence[uuid.UUID]
    ) -> Sequence[tuple[uuid.UUID, str]]:
        """Retorna (id, code) das posicoes existentes entre os ids informados."""
        if not position_ids:
            return []
        result = await self.db.execute(
            select(Position.id, Position.code).where(Position.id.in_(position_ids))
        )
        return result.all()

    async def get_team_cycle_season_in_current_season(
        self, team_cycle_season_id: uuid.UUID
    ) -> TeamCycleSeason | None:
        """Retorna o TeamCycleSeason se ele pertencer a temporada atual."""
        result = await self.db.execute(
            select(TeamCycleSeason)
            .join(CycleSeason, CycleSeason.id == TeamCycleSeason.cycle_season_id)
            .where(TeamCycleSeason.id == team_cycle_season_id)
            .where(CycleSeason.end_date.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_current_season_squad(
        self, player_id: uuid.UUID
    ) -> TeamSquad | None:
        """TeamSquad do jogador na temporada atual (CycleSeason.endDate nulo)."""
        result = await self.db.execute(
            select(TeamSquad)
            .join(
                TeamCycleSeason,
                TeamCycleSeason.id == TeamSquad.team_cycle_season_id,
            )
            .join(CycleSeason, CycleSeason.id == TeamCycleSeason.cycle_season_id)
            .where(TeamSquad.player_id == player_id)
            .where(CycleSeason.end_date.is_(None))
            .order_by(TeamSquad.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_team_name(self, team_cycle_season_id: uuid.UUID) -> str | None:
        """Nome do Team ligado ao TeamCycleSeason."""
        result = await self.db.execute(
            select(Team.name)
            .join(TeamCycleSeason, TeamCycleSeason.team_id == Team.id)
            .where(TeamCycleSeason.id == team_cycle_season_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        overall_id: uuid.UUID,
        position_ids: Sequence[uuid.UUID],
    ) -> Player:
        """Insere Player e as linhas de PlayerPosition correspondentes."""
        player = Player(name=name, overall_id=overall_id)
        self.db.add(player)
        await self.db.flush()

        for position_id in position_ids:
            self.db.add(
                PlayerPosition(player_id=player.id, position_id=position_id)
            )

        await self.db.commit()
        await self.db.refresh(player)
        return player

    async def update(
        self,
        player: Player,
        name: str,
        overall_id: uuid.UUID,
        position_ids: Sequence[uuid.UUID],
        team_cycle_season_id: uuid.UUID | None,
    ) -> Player:
        """Atualiza nome, overall, posicoes e, se informado, o TeamSquad
        da temporada atual (update da coluna ou insert de nova linha)."""
        player.name = name
        player.overall_id = overall_id
        player.updated_at = datetime.now(timezone.utc)

        await self.db.execute(
            delete(PlayerPosition).where(PlayerPosition.player_id == player.id)
        )
        for position_id in position_ids:
            self.db.add(
                PlayerPosition(player_id=player.id, position_id=position_id)
            )

        if team_cycle_season_id is not None:
            current_squad = await self.get_current_season_squad(player.id)
            if current_squad is not None:
                current_squad.team_cycle_season_id = team_cycle_season_id
            else:
                self.db.add(
                    TeamSquad(
                        player_id=player.id,
                        team_cycle_season_id=team_cycle_season_id,
                    )
                )

        await self.db.commit()
        await self.db.refresh(player)
        return player

    async def delete(self, player: Player) -> None:
        """Remove MatchPlayerStat, PlayerPosition, TeamSquad e depois o Player."""
        player_id = player.id

        await self.db.execute(
            delete(MatchPlayerStat).where(MatchPlayerStat.player_id == player_id)
        )
        await self.db.execute(
            delete(PlayerPosition).where(PlayerPosition.player_id == player_id)
        )
        await self.db.execute(
            delete(TeamSquad).where(TeamSquad.player_id == player_id)
        )
        await self.db.delete(player)
        await self.db.commit()
