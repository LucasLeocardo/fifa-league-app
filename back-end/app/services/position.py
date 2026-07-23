"""Camada de servico de Position."""

from __future__ import annotations

from app.repositories.position import PositionRepository
from app.schemas.position import PositionRead


class PositionService:
    def __init__(self, repository: PositionRepository) -> None:
        self.repository = repository

    async def list_all(self) -> list[PositionRead]:
        """Lista todas as posicoes (id e code)."""
        rows = await self.repository.list_all()
        return [PositionRead(id=row.id, code=row.code) for row in rows]
