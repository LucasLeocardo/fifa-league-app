"""Camada de servico de File (upload de fotos de partida)."""

from __future__ import annotations

import csv
import io
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.storage import build_match_photo_path, download_bytes, upload_bytes
from app.models.match import Match
from app.models.team_cycle_season import TeamCycleSeason
from app.repositories.file import FileRepository
from app.schemas.file import FilePendingChildRead, FileRead, MatchPlayerRatingRow


class FileService:
    def __init__(self, db: AsyncSession, repository: FileRepository) -> None:
        self.db = db
        self.repository = repository

    async def list_unprocessed_children(self) -> list[FilePendingChildRead]:
        """Lista Files com parentId preenchido e isProcessed = false."""
        rows = await self.repository.list_unprocessed_with_parent()
        return [
            FilePendingChildRead(file_id=row.id, name=row.name) for row in rows
        ]

    async def get_csv_ratings(
        self, file_id: uuid.UUID
    ) -> list[MatchPlayerRatingRow]:
        """Baixa o CSV do File e devolve as linhas de desempenho.

        Colunas de saida: position, playerName, goals, assists, averageRating.
        O CSV do OCR usa cabecalhos POS, Name, NF, G, AST.
        """
        row = await self.repository.get_by_id(file_id)
        if row is None:
            raise NotFoundError("Arquivo nao encontrado.")

        content = download_bytes(file_url=row.url)
        if not content:
            raise BadRequestError("Arquivo CSV vazio.")

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise BadRequestError(
                "Nao foi possivel ler o CSV (encoding invalido)."
            ) from exc

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise BadRequestError("CSV sem cabecalho.")

        field_map = {
            _normalize_header(name): name for name in reader.fieldnames
        }
        required = {
            "pos": "POS",
            "name": "Name",
            "nf": "NF",
            "g": "G",
            "ast": "AST",
        }
        resolved: dict[str, str] = {}
        for key, label in required.items():
            if key not in field_map:
                raise BadRequestError(
                    f"CSV sem a coluna obrigatoria '{label}'."
                )
            resolved[key] = field_map[key]

        ratings: list[MatchPlayerRatingRow] = []
        for csv_row in reader:
            position = (csv_row.get(resolved["pos"]) or "").strip()
            player_name = (csv_row.get(resolved["name"]) or "").strip()
            if not player_name:
                continue
            ratings.append(
                MatchPlayerRatingRow(
                    file_id=row.id,
                    source_game_id=row.source_game_id,
                    team_cycle_season_id=row.team_cycle_season_id,
                    position=position,
                    player_name=player_name,
                    goals=_parse_int(csv_row.get(resolved["g"])),
                    assists=_parse_int(csv_row.get(resolved["ast"])),
                    average_rating=_parse_rating(csv_row.get(resolved["nf"])),
                )
            )
        return ratings

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

            created_row = await self.repository.create(
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
                    file_id=created_row.id,
                    name=created_row.name,
                    extension=created_row.extension,
                    mime_type=created_row.mime_type,
                    url=created_row.url,
                    source_game_id=created_row.source_game_id,
                    team_cycle_season_id=created_row.team_cycle_season_id,
                    is_processed=created_row.is_processed,
                )
            )
        return created


def _normalize_header(value: str) -> str:
    return value.strip().lower()


def _parse_int(value: str | None) -> int:
    if value is None:
        return 0
    digits = "".join(ch for ch in value.strip() if ch.isdigit())
    return int(digits) if digits else 0


def _parse_rating(value: str | None) -> float | None:
    if value is None:
        return None
    raw = value.strip().upper().replace(",", ".")
    if not raw or raw in {"ND", "N/A", "NA", "-", "--"}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


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
