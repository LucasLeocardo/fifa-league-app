"""Schemas Pydantic do elenco (TeamSquad)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SquadPlayerRead(_CamelModel):
    """Jogador do elenco com dados agregados."""

    team_squad_id: uuid.UUID
    player_name: str = Field(..., max_length=255)
    overall: int | None = None
    player_cost: int | None = None
    currency: str | None = Field(default=None, max_length=255)
    shirt_number: int | None = None
    positions: list[str] = Field(default_factory=list)
    total_goals: int = 0
    total_assists: int = 0
    average_rating: float | None = None


class SquadResponse(_CamelModel):
    """Resposta do endpoint de elenco."""

    team_cycle_season_id: uuid.UUID
    players: list[SquadPlayerRead]


class ShirtNumberUpdate(_CamelModel):
    """Corpo para atualizar o numero da camisa de uma linha de TeamSquad."""

    shirt_number: int = Field(..., ge=0)


class TeamSquadEntryRead(_CamelModel):
    """Linha de TeamSquad apos atualizacao."""

    team_squad_id: uuid.UUID
    shirt_number: int | None = None
