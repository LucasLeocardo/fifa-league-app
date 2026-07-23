"""Schemas Pydantic de Match."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class MatchRead(_CamelModel):
    """Partida com placar, nomes dos times e tipo."""

    match_id: uuid.UUID
    home_team_name: str = Field(..., max_length=255)
    away_team_name: str = Field(..., max_length=255)
    home_score: int | None = None
    away_score: int | None = None
    match_type_name: str | None = Field(default=None, max_length=255)


class MatchCreate(_CamelModel):
    """Payload para criar uma nova partida."""

    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    match_type_id: uuid.UUID
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
