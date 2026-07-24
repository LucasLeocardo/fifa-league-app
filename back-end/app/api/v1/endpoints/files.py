"""Camada de rotas de File (upload de fotos de partida)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.deps import CurrentUserDep, FileServiceDep, MatchPlayerStatServiceDep
from app.schemas.file import (
    ConfirmPlayerStatsPayload,
    FilePendingChildRead,
    FileRead,
    MatchPlayerRatingRow,
    MatchPlayerStatRead,
)

router = APIRouter()


@router.get(
    "/pending-children",
    summary="Lista Files filhos ainda nao processados",
)
async def list_pending_children(
    service: FileServiceDep,
    _current_user: CurrentUserDep,
) -> list[FilePendingChildRead]:
    """Retorna fileId e name de Files com parentId preenchido e isProcessed=false."""
    return await service.list_unprocessed_children()


@router.get(
    "/{file_id}/ratings",
    summary="Baixa o CSV do File e retorna a tabela de desempenho",
)
async def get_file_ratings(
    file_id: uuid.UUID,
    service: FileServiceDep,
    _current_user: CurrentUserDep,
) -> list[MatchPlayerRatingRow]:
    """Processa o CSV e devolve posicao, nome, gols, assistencias e media."""
    return await service.get_csv_ratings(file_id)


@router.post(
    "/confirm-ratings",
    status_code=status.HTTP_201_CREATED,
    summary="Confirma ratings OCR, grava MatchPlayerStat e marca File",
)
async def confirm_file_ratings(
    payload: ConfirmPlayerStatsPayload,
    service: MatchPlayerStatServiceDep,
    _current_user: CurrentUserDep,
) -> list[MatchPlayerStatRead]:
    """Resolve jogadores por nome (matching flexivel), cria stats e processa o File.

    Se algum nome nao for encontrado de forma unica/confiavel, retorna 400.
    """
    return await service.confirm_from_ocr(payload)


@router.post(
    "/upload-photos",
    status_code=status.HTTP_201_CREATED,
    summary="Faz upload de fotos de uma partida e grava em File",
)
async def upload_match_photos(
    service: FileServiceDep,
    _current_user: CurrentUserDep,
    photos: Annotated[
        list[UploadFile],
        File(description="Lista de fotos da partida"),
    ],
    source_game_id: Annotated[uuid.UUID, Form(alias="sourceGameId")],
    team_cycle_season_id: Annotated[
        uuid.UUID,
        Form(alias="teamCycleSeasonId"),
    ],
) -> list[FileRead]:
    """Recebe lista de fotos + sourceGameId + teamCycleSeasonId.

    Faz upload de cada imagem no bucket do Supabase Storage e cria a linha
    correspondente em File (name, mimeType, extension, url, sourceGameId,
    teamCycleSeasonId).
    """
    packed: list[tuple[bytes, str | None, str | None]] = []
    for photo in photos:
        packed.append(
            (await photo.read(), photo.filename, photo.content_type)
        )

    return await service.upload_match_photos(
        photos=packed,
        source_game_id=source_game_id,
        team_cycle_season_id=team_cycle_season_id,
    )
