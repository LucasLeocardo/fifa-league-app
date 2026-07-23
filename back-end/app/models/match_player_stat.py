"""Modelo ORM da tabela "MatchPlayerStat"."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, Float, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MatchPlayerStat(Base):
    __tablename__ = "MatchPlayerStat"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        "matchId", UUID(as_uuid=True), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        "playerId", UUID(as_uuid=True), nullable=False
    )
    team_squad_id: Mapped[uuid.UUID | None] = mapped_column(
        "teamSquadId", UUID(as_uuid=True), nullable=True
    )
    source_file: Mapped[uuid.UUID | None] = mapped_column(
        "sourceFile", UUID(as_uuid=True), nullable=True
    )
    goals: Mapped[int | None] = mapped_column("goals", Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column("assists", Integer, nullable=True)
    rating: Mapped[float | None] = mapped_column("rating", Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
