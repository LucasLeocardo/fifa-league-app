"""Modelo ORM da view "TeamStandings" (somente leitura)."""

import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TeamStanding(Base):
    """Linha da classificacao por TeamCycleSeason.

    A view nao e gravavel: use apenas em SELECT via repositorio.
    """

    __tablename__ = "TeamStandings"

    team_cycle_season_id: Mapped[uuid.UUID] = mapped_column(
        "teamCycleSeasonId",
        UUID(as_uuid=True),
        primary_key=True,
    )
    cycle_season_id: Mapped[uuid.UUID] = mapped_column(
        "cycleSeasonId", UUID(as_uuid=True), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        "teamId", UUID(as_uuid=True), nullable=False
    )
    team_name: Mapped[str] = mapped_column("teamName", String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        "userId", UUID(as_uuid=True), nullable=False
    )
    coach_name: Mapped[str | None] = mapped_column(
        "coachName", String(255), nullable=True
    )
    points: Mapped[int] = mapped_column("points", Integer, nullable=False)
    wins: Mapped[int] = mapped_column("wins", Integer, nullable=False)
    draws: Mapped[int] = mapped_column("draws", Integer, nullable=False)
    losses: Mapped[int] = mapped_column("losses", Integer, nullable=False)
    goals_for: Mapped[int] = mapped_column("goalsFor", Integer, nullable=False)
    goals_against: Mapped[int] = mapped_column("goalsAgainst", Integer, nullable=False)
    goal_difference: Mapped[int] = mapped_column(
        "goalDifference", Integer, nullable=False
    )
