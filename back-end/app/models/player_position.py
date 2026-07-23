"""Modelo ORM da tabela "PlayerPosition"."""

import uuid
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlayerPosition(Base):
    __tablename__ = "PlayerPosition"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        "playerId", UUID(as_uuid=True), nullable=False
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        "positionId", UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
