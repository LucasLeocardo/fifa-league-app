"""Modelo ORM da tabela "Match"."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Match(Base):
    __tablename__ = "Match"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    home_team_id: Mapped[uuid.UUID | None] = mapped_column(
        "homeTeamId", UUID(as_uuid=True), nullable=True
    )
    away_team_id: Mapped[uuid.UUID | None] = mapped_column(
        "awayTeamId", UUID(as_uuid=True), nullable=True
    )
    type_id: Mapped[uuid.UUID | None] = mapped_column(
        "typeId", UUID(as_uuid=True), nullable=True
    )
    home_score: Mapped[int | None] = mapped_column(
        "homeScore", Integer, nullable=True
    )
    away_score: Mapped[int | None] = mapped_column(
        "awayScore", Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
