"""Camada de acesso a dados de Position."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position


class PositionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> Sequence[Position]:
        """Lista todas as posicoes ordenadas pelo code."""
        result = await self.db.execute(
            select(Position).order_by(Position.code.asc())
        )
        return result.scalars().all()
