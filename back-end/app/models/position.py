"""Modelo ORM da tabela "Position"."""

import uuid
from datetime import datetime

from sqlalchemy import String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Position(Base):
    __tablename__ = "Position"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column("code", String(255), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
