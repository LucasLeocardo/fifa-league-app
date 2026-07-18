"""Schemas Pydantic da classificacao (TeamStandings)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class TeamStandingRead(_CamelModel):
    team_cycle_season_id: uuid.UUID
    cycle_season_id: uuid.UUID
    team_id: uuid.UUID
    team_name: str = Field(..., max_length=255)
    user_id: uuid.UUID
    coach_name: str | None = Field(default=None, max_length=255)
    points: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int


class StandingsResponse(_CamelModel):
    """Resposta do endpoint de classificacao."""

    cycle_season_id: uuid.UUID
    standings: list[TeamStandingRead]
