"""Camada de servico de CycleSeason."""

from __future__ import annotations

from app.repositories.cycle_season import CycleSeasonRepository
from app.schemas.cycle_season import CycleSeasonRead


class CycleSeasonService:
    def __init__(self, repository: CycleSeasonRepository) -> None:
        self.repository = repository

    async def list_all(self) -> list[CycleSeasonRead]:
        """Retorna todas as CycleSeasons com nome do ciclo e da temporada."""
        rows = await self.repository.list_with_names()
        return [
            CycleSeasonRead(
                cycle_season_id=row.cycle_season_id,
                cycle_name=row.cycle_name,
                season_name=row.season_name,
                is_current_season=row.is_current_season,
            )
            for row in rows
        ]
