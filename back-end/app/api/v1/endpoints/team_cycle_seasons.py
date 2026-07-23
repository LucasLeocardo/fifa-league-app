"""Camada de rotas de TeamCycleSeason: apenas HTTP (delega ao service)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, TeamCycleSeasonServiceDep
from app.schemas.team_cycle_season import TeamCycleSeasonRead

router = APIRouter()


@router.get(
    "",
    summary="Lista os TeamCycleSeason de uma temporada",
)
async def list_team_cycle_seasons(
    service: TeamCycleSeasonServiceDep,
    current_user: CurrentUserDep,
    cycle_season_id: Annotated[
        uuid.UUID | None,
        Query(
            alias="cycleSeasonId",
            description=(
                "Se informado, lista os TeamCycleSeason desse CycleSeason. "
                "Se omitido, usa a temporada atual (CycleSeason com endDate nulo)."
            ),
        ),
    ] = None,
) -> list[TeamCycleSeasonRead]:
    """Retorna teamCycleSeasonId, teamName e isMyTeam.

    isMyTeam e true quando a linha pertence ao userId do token.
    """
    return await service.list_current_for_user(current_user.id, cycle_season_id)
