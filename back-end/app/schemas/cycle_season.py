"""Schemas Pydantic de CycleSeason."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class CycleSeasonRead(_CamelModel):
    """CycleSeason com os nomes do ciclo e da temporada."""

    cycle_season_id: uuid.UUID
    cycle_name: str = Field(..., max_length=255)
    season_name: str = Field(..., max_length=255)
    is_current_season: bool
