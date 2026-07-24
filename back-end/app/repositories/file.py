"""Camada de acesso a dados de File."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
