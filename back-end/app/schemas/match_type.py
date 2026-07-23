"""Schemas Pydantic de MatchType."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class MatchTypeRead(_CamelModel):
    """Tipo de partida com id e nome."""

    match_type_id: uuid.UUID
    name: str = Field(..., max_length=255)
