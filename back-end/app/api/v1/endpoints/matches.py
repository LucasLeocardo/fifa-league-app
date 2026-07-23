"""Camada de rotas de Match."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentAdminUserDep, CurrentUserDep, MatchServiceDep
from app.schemas.match import MatchCreate, MatchRead

router = APIRouter()


@router.get(
    "",
    summary="Lista as partidas de um TeamCycleSeason",
)
async def list_matches(
    service: MatchServiceDep,
    current_user: CurrentUserDep,
    team_cycle_season_id: Annotated[
        uuid.UUID | None,
        Query(
            alias="teamCycleSeasonId",
            description=(
                "Se informado, lista partidas desse TeamCycleSeason. "
                "Se omitido, usa o TeamCycleSeason do usuario (do token) "
                "na temporada atual (CycleSeason com endDate nulo)."
            ),
        ),
    ] = None,
) -> list[MatchRead]:
    """Retorna placar, nomes dos times e nome do MatchType de cada partida."""
    return await service.list_matches(current_user.id, team_cycle_season_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova partida",
)
async def create_match(
    service: MatchServiceDep,
    _current_admin: CurrentAdminUserDep,
    payload: MatchCreate,
) -> MatchRead:
    """Recebe homeTeamId, awayTeamId, matchTypeId, homeScore e awayScore.

    Somente usuarios com isAdmin = true (do token) podem criar partidas.
    """
    return await service.create_match(payload)
