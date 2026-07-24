"""Schemas Pydantic de File."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class FileRead(_CamelModel):
    """Linha da tabela File apos upload."""

    file_id: uuid.UUID
    name: str = Field(..., max_length=255)
    extension: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)
    url: str
    source_game_id: uuid.UUID | None = None
    team_cycle_season_id: uuid.UUID | None = None
    is_processed: bool = False
