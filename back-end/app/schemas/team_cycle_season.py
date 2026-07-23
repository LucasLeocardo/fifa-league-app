"""Schemas Pydantic de TeamCycleSeason."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class TeamCycleSeasonRead(_CamelModel):
    """TeamCycleSeason da temporada atual com o nome do time."""

    team_cycle_season_id: uuid.UUID
    team_name: str = Field(..., max_length=255)
    is_my_team: bool
