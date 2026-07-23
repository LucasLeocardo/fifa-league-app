"""Modelo ORM da tabela "TeamCycleSeason"."""

import uuid
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TeamCycleSeason(Base):
    __tablename__ = "TeamCycleSeason"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        "teamId", UUID(as_uuid=True), nullable=False
    )
    cycle_season_id: Mapped[uuid.UUID] = mapped_column(
        "cycleSeasonId", UUID(as_uuid=True), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "userId", UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
