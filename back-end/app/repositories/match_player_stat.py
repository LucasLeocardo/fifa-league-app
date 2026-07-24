"""Camada de acesso a dados de MatchPlayerStat."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_player_stat import MatchPlayerStat


class MatchPlayerStatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_existing_match_player_pairs(
        self,
        pairs: Sequence[tuple[uuid.UUID, uuid.UUID]],
    ) -> set[tuple[uuid.UUID, uuid.UUID]]:
        """Retorna o subconjunto de (matchId, playerId) que ja existe."""
        if not pairs:
            return set()
        result = await self.db.execute(
            select(MatchPlayerStat.match_id, MatchPlayerStat.player_id).where(
                tuple_(MatchPlayerStat.match_id, MatchPlayerStat.player_id).in_(
                    list(pairs)
                )
            )
        )
        return {(row[0], row[1]) for row in result.all()}

    async def create_many(
        self,
        rows: Sequence[MatchPlayerStat],
        *,
        commit: bool = True,
    ) -> list[MatchPlayerStat]:
        """Insere varias linhas de MatchPlayerStat."""
        self.db.add_all(list(rows))
        if commit:
            await self.db.commit()
            for row in rows:
                await self.db.refresh(row)
        else:
            await self.db.flush()
            for row in rows:
                await self.db.refresh(row)
        return list(rows)
