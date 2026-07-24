"""Camada de acesso a dados de File."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_unprocessed_with_parent(self) -> Sequence[File]:
        """Lista Files com parentId preenchido e isProcessed = false."""
        result = await self.db.execute(
            select(File)
            .where(File.parent_id.is_not(None))
            .where(File.is_processed.is_(False))
            .order_by(File.created_at.asc(), File.id.asc())
        )
        return result.scalars().all()

    async def get_by_id(self, file_id: uuid.UUID) -> File | None:
        """Busca um File pelo id."""
        return await self.db.get(File, file_id)

    async def mark_processed(
        self, file_id: uuid.UUID, *, commit: bool = True
    ) -> File | None:
        """Define isProcessed = true para o File informado."""
        row = await self.get_by_id(file_id)
        if row is None:
            return None
        row.is_processed = True
        if commit:
            await self.db.commit()
            await self.db.refresh(row)
        else:
            await self.db.flush()
            await self.db.refresh(row)
        return row

    async def create(
        self,
        *,
        name: str,
        url: str,
        extension: str | None,
        mime_type: str | None,
        source_game_id: uuid.UUID,
        team_cycle_season_id: uuid.UUID,
        is_processed: bool = False,
    ) -> File:
        """Insere uma linha em File e retorna a entidade persistida."""
        row = File(
            name=name,
            url=url,
            extension=extension,
            mime_type=mime_type,
            source_game_id=source_game_id,
            team_cycle_season_id=team_cycle_season_id,
            is_processed=is_processed,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row
