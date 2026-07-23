"""Camada de rotas do elenco (TeamSquad): apenas HTTP (delega ao service)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import CurrentUserDep, TeamSquadServiceDep
from app.schemas.team_squad import (
    ShirtNumberUpdate,
    SquadResponse,
    TeamSquadEntryRead,
)

router = APIRouter()


@router.get(
    "",
    summary="Lista os jogadores de um elenco (TeamSquad)",
)
async def get_squad(
    service: TeamSquadServiceDep,
    current_user: CurrentUserDep,
    team_cycle_season_id: Annotated[
        uuid.UUID | None,
        Query(
            alias="teamCycleSeasonId",
            description=(
                "Se informado, lista o elenco desse TeamCycleSeason. Se omitido, "
                "usa o TeamCycleSeason do usuario (do token) na temporada atual "
                "(CycleSeason com endDate nulo)."
            ),
        ),
    ] = None,
) -> SquadResponse:
    """Retorna nome, overall, numero da camisa, posicoes (array) e teamSquadId."""
    return await service.get_squad(current_user.id, team_cycle_season_id)


@router.patch(
    "/{team_squad_id}",
    summary="Atualiza o numero da camisa (shirtNumber) de uma linha de TeamSquad",
)
async def update_shirt_number(
    service: TeamSquadServiceDep,
    _current_user: CurrentUserDep,
    payload: ShirtNumberUpdate,
    team_squad_id: Annotated[
        uuid.UUID,
        Path(description="Id da linha em TeamSquad."),
    ],
) -> TeamSquadEntryRead:
    """Atualiza o shirtNumber do TeamSquad informado."""
    return await service.update_shirt_number(team_squad_id, payload.shirt_number)
