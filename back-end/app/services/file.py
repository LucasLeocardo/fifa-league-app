"""Camada de servico de File (upload de fotos de partida)."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.storage import build_match_photo_path, upload_bytes
from app.models.match import Match
from app.models.team_cycle_season import TeamCycleSeason
from app.repositories.file import FileRepository
from app.schemas.file import FileRead


class FileService:
    def __init__(self, db: AsyncSession, repository: FileRepository) -> None:
        self.db = db
        self.repository = repository

    async def upload_match_photos(
        self,
        *,
        photos: list[tuple[bytes, str | None, str | None]],
        source_game_id: uuid.UUID,
        team_cycle_season_id: uuid.UUID,
    ) -> list[FileRead]:
        """Faz upload das fotos no Storage e cria linhas em File.

        Cada item de `photos` e (conteudo, filename, content_type).
        """
        if not photos:
            raise BadRequestError("Envie ao menos uma foto.")

        match = await self.db.get(Match, source_game_id)
        if match is None:
            raise NotFoundError("Partida (sourceGameId) nao encontrada.")

        tcs = await self.db.execute(
            select(TeamCycleSeason.id).where(
                TeamCycleSeason.id == team_cycle_season_id
            )
        )
        if tcs.scalar_one_or_none() is None:
            raise NotFoundError(
                "TeamCycleSeason (teamCycleSeasonId) nao encontrado."
            )

        created: list[FileRead] = []
        for content, original_filename, content_type in photos:
            if not content:
                raise BadRequestError("Uma das fotos enviadas esta vazia.")

            file_name = Path(original_filename or "photo").name or "photo"
            extension = Path(file_name).suffix.lstrip(".") or None
            mime_type = content_type or _guess_mime_type(extension)

            object_path = build_match_photo_path(source_game_id, file_name)
            file_url = upload_bytes(
                content=content,
                object_path=object_path,
                content_type=mime_type or "application/octet-stream",
            )

            row = await self.repository.create(
                name=file_name,
                url=file_url,
                extension=extension,
                mime_type=mime_type,
                source_game_id=source_game_id,
                team_cycle_season_id=team_cycle_season_id,
                is_processed=False,
            )
            created.append(
                FileRead(
                    file_id=row.id,
                    name=row.name,
                    extension=row.extension,
                    mime_type=row.mime_type,
                    url=row.url,
                    source_game_id=row.source_game_id,
                    team_cycle_season_id=row.team_cycle_season_id,
                    is_processed=row.is_processed,
                )
            )
        return created


def _guess_mime_type(extension: str | None) -> str | None:
    if not extension:
        return None
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "heic": "image/heic",
    }
    return mapping.get(extension.lower())
