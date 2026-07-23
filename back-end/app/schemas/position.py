"""Schemas Pydantic de Position."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PositionRead(_CamelModel):
    """Posicao com id e code."""

    id: uuid.UUID
    code: str = Field(..., max_length=255)
