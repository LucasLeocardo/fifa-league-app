"""Modelo ORM da tabela "CycleSeason"."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CycleSeason(Base):
    __tablename__ = "CycleSeason"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        "cycleId", UUID(as_uuid=True), nullable=False
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        "seasonId", UUID(as_uuid=True), nullable=False
    )
    start_date: Mapped[date] = mapped_column("startDate", Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column("endDate", Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
