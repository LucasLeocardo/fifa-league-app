"""Camada de rotas de CycleSeason: apenas HTTP (delega ao service)."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, CycleSeasonServiceDep
from app.schemas.cycle_season import CycleSeasonRead

router = APIRouter()


@router.get(
    "",
    summary="Lista todas as CycleSeasons (com nome do ciclo e da temporada)",
)
async def list_cycle_seasons(
    service: CycleSeasonServiceDep,
    _current_user: CurrentUserDep,
) -> list[CycleSeasonRead]:
    """Retorna cycleSeasonId, cycleName e seasonName de todas as CycleSeasons."""
    return await service.list_all()
