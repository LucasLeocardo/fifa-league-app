"""Camada de rotas de Player."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import CurrentAdminUserDep, CurrentUserDep, PlayerServiceDep
from app.schemas.player import PlayerCreate, PlayerSearchRead, PlayerUpdate

router = APIRouter()


@router.get(
    "",
    summary="Busca jogadores pelo nome (contains)",
)
async def search_players(
    service: PlayerServiceDep,
    _current_user: CurrentUserDep,
    name: Annotated[
        str,
        Query(
            description=(
                "Trecho do nome do jogador. Filtra Player.name com ILIKE "
                "(%name%), retornando quem contains o texto."
            ),
            min_length=1,
            max_length=255,
        ),
    ],
) -> list[PlayerSearchRead]:
    """Retorna nome, overall, posicoes e time na temporada atual (opcional)."""
    return await service.search_by_name(name)


@router.get(
    "/{player_id}",
    summary="Detalhe de um jogador pelo id",
)
async def get_player(
    service: PlayerServiceDep,
    _current_user: CurrentUserDep,
    player_id: Annotated[
        uuid.UUID,
        Path(description="Id do jogador."),
    ],
) -> PlayerSearchRead:
    """Retorna nome, overall, posicoes e time na temporada atual."""
    return await service.get_player(player_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo jogador",
)
async def create_player(
    service: PlayerServiceDep,
    _current_admin: CurrentAdminUserDep,
    payload: PlayerCreate,
) -> PlayerSearchRead:
    """Recebe name, overall (value) e positionIds.

    Resolve Overall pelo value, valida as posicoes e grava Player +
    PlayerPosition. Somente admins podem cadastrar.
    """
    return await service.create_player(payload)


@router.patch(
    "/{player_id}",
    summary="Atualiza um jogador existente",
)
async def update_player(
    service: PlayerServiceDep,
    _current_admin: CurrentAdminUserDep,
    payload: PlayerUpdate,
    player_id: Annotated[
        uuid.UUID,
        Path(description="Id do jogador a atualizar."),
    ],
) -> PlayerSearchRead:
    """Atualiza name, overall, positionIds e opcionalmente teamCycleSeasonId.

    Se teamCycleSeasonId for informado:
    - com TeamSquad na temporada atual: atualiza teamCycleSeasonId;
    - sem TeamSquad na temporada atual: cria a linha.
    Somente admins podem atualizar.
    """
    return await service.update_player(player_id, payload)


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um jogador",
)
async def delete_player(
    service: PlayerServiceDep,
    current_admin: CurrentAdminUserDep,
    player_id: Annotated[
        uuid.UUID,
        Path(description="Id do jogador a remover."),
    ],
) -> None:
    """Remove MatchPlayerStat, PlayerPosition e TeamSquad e depois o Player.

    Exige admin e que o name do usuario autenticado seja exatamente Leocardo.
    """
    await service.delete_player(player_id, current_admin.name)
