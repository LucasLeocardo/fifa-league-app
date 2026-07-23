"""Camada de rotas do leaderboard (gols, assistencias e notas)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, LeaderboardServiceDep
from app.schemas.leaderboard import LeaderboardResponse

router = APIRouter()


@router.get(
    "",
    summary="Leaderboard de gols, assistencias e notas medias da CycleSeason",
)
async def get_leaderboard(
    service: LeaderboardServiceDep,
    _current_user: CurrentUserDep,
    cycle_season_id: Annotated[
        uuid.UUID | None,
        Query(
            alias="cycleSeasonId",
            description=(
                "Se omitido, usa a CycleSeason aberta (endDate nulo). "
                "Se informado, monta o leaderboard dessa temporada."
            ),
        ),
    ] = None,
    position_ids: Annotated[
        list[uuid.UUID] | None,
        Query(
            alias="positionIds",
            description=(
                "Lista de Position.id. Se vazia ou omitida, nao filtra. "
                "Se informada, so entram jogadores com ao menos uma dessas "
                "posicoes."
            ),
        ),
    ] = None,
) -> LeaderboardResponse:
    """Retorna 3 listas: gols, assistencias e notas medias.

    Na lista de notas, so entram jogadores com jogos >= 75% do total de
    partidas do time que mais jogou no campeonato.
    """
    return await service.get_leaderboard(cycle_season_id, position_ids)
