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


class FilePendingChildRead(_CamelModel):
    """File filho (parentId preenchido) ainda nao processado."""

    file_id: uuid.UUID
    name: str = Field(..., max_length=255)


class MatchPlayerRatingRow(_CamelModel):
    """Linha de desempenho individual extraida do CSV do OCR."""

    file_id: uuid.UUID
    source_game_id: uuid.UUID | None = None
    team_cycle_season_id: uuid.UUID | None = None
    position: str = Field(..., max_length=32)
    player_name: str = Field(..., max_length=255)
    goals: int = Field(..., ge=0)
    assists: int = Field(..., ge=0)
    average_rating: float | None = None


class ConfirmPlayerStatItem(_CamelModel):
    """Linha confirmada pelo front para gravar em MatchPlayerStat."""

    player_name: str = Field(..., min_length=1, max_length=255)
    goals: int = Field(..., ge=0)
    assists: int = Field(..., ge=0)
    average_rating: float | None = None
    source_game_id: uuid.UUID
    team_cycle_season_id: uuid.UUID


class ConfirmPlayerStatsPayload(_CamelModel):
    """Payload para confirmar ratings OCR e gravar MatchPlayerStat."""

    file_id: uuid.UUID
    players: list[ConfirmPlayerStatItem] = Field(..., min_length=1)


class MatchPlayerStatRead(_CamelModel):
    """Linha criada em MatchPlayerStat."""

    match_player_stat_id: uuid.UUID
    match_id: uuid.UUID
    player_id: uuid.UUID
    player_name: str
    team_squad_id: uuid.UUID | None = None
    source_file: uuid.UUID | None = None
    goals: int | None = None
    assists: int | None = None
    rating: float | None = None
