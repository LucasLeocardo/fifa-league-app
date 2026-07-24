"""Camada de rotas de File (upload de fotos de partida)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.deps import CurrentUserDep, FileServiceDep
from app.schemas.file import FileRead

router = APIRouter()


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
