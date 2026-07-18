"""Camada de rotas da classificacao (TeamStandings)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, TeamStandingServiceDep
from app.schemas.team_standing import StandingsResponse

router = APIRouter()


@router.get(
    "",
    summary="Lista a classificacao de uma CycleSeason",
)
async def get_standings(
    service: TeamStandingServiceDep,
    _current_user: CurrentUserDep,
    cycle_season_id: Annotated[
        uuid.UUID | None,
        Query(
            alias="cycleSeasonId",
            description=(
                "Se omitido, usa a CycleSeason aberta (endDate nulo). "
                "Se informado, filtra a view TeamStandings por esse id."
            ),
        ),
    ] = None,
) -> StandingsResponse:
    """Retorna times ordenados por pontos, saldo e gols.

    Sem `cycleSeasonId`, resolve a temporada ativa em `CycleSeason` onde
    `endDate` e nulo e filtra a view com esse id.
    """
    return await service.get_standings(cycle_season_id)
