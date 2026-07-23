"""Modelo ORM da tabela "Overall"."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Overall(Base):
    __tablename__ = "Overall"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    value: Mapped[int] = mapped_column("value", Integer, nullable=False)
    player_cost: Mapped[int] = mapped_column("playerCost", Integer, nullable=False)
    currency: Mapped[str | None] = mapped_column(
        "currency", String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
