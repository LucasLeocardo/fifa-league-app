"""Modelo ORM da tabela "Player"."""

import uuid
from datetime import datetime

from sqlalchemy import String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Player(Base):
    __tablename__ = "Player"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    overall_id: Mapped[uuid.UUID | None] = mapped_column(
        "overallId", UUID(as_uuid=True), nullable=True
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
