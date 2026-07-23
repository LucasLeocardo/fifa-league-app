"""Modelo ORM da tabela "TeamSquad"."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TeamSquad(Base):
    __tablename__ = "TeamSquad"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    team_cycle_season_id: Mapped[uuid.UUID] = mapped_column(
        "teamCycleSeasonId", UUID(as_uuid=True), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        "playerId", UUID(as_uuid=True), nullable=False
    )
    shirt_number: Mapped[int | None] = mapped_column(
        "shirtNumber", Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
