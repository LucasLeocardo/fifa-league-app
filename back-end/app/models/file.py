"""Modelo ORM da tabela "File"."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class File(Base):
    __tablename__ = "File"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        "parentId", UUID(as_uuid=True), nullable=True
    )
    source_game_id: Mapped[uuid.UUID | None] = mapped_column(
        "sourceGameId", UUID(as_uuid=True), nullable=True
    )
    team_cycle_season_id: Mapped[uuid.UUID | None] = mapped_column(
        "teamCycleSeasonId", UUID(as_uuid=True), nullable=True
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    extension: Mapped[str | None] = mapped_column(
        "extension", String(255), nullable=True
    )
    mime_type: Mapped[str | None] = mapped_column(
        "mimeType", String(255), nullable=True
    )
    url: Mapped[str] = mapped_column("url", Text, nullable=False)
    is_processed: Mapped[bool] = mapped_column(
        "isProcessed",
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
