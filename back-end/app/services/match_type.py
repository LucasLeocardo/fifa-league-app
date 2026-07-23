"""Camada de servico de MatchType."""

from __future__ import annotations

from app.repositories.match_type import MatchTypeRepository
from app.schemas.match_type import MatchTypeRead


class MatchTypeService:
    def __init__(self, repository: MatchTypeRepository) -> None:
        self.repository = repository

    async def list_all(self) -> list[MatchTypeRead]:
        """Lista todos os MatchTypes (matchTypeId e name)."""
        rows = await self.repository.list_all()
        return [
            MatchTypeRead(match_type_id=row.id, name=row.name) for row in rows
        ]
