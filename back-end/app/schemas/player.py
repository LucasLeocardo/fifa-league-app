"""Schemas Pydantic de Player (busca e cadastro)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PlayerSearchRead(_CamelModel):
    """Jogador encontrado na busca por nome."""

    player_id: uuid.UUID
    player_name: str = Field(..., max_length=255)
    overall: int | None = None
    positions: list[str] = Field(default_factory=list)
    position_ids: list[uuid.UUID] = Field(default_factory=list)
    team_name: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Nome do time na temporada atual (CycleSeason com endDate nulo). "
            "Null se o jogador nao estiver em nenhum elenco da temporada atual."
        ),
    )
    team_cycle_season_id: uuid.UUID | None = Field(
        default=None,
        description="TeamCycleSeason do time na temporada atual, se houver.",
    )


class PlayerCreate(_CamelModel):
    """Payload para cadastrar um novo jogador."""

    name: str = Field(..., min_length=1, max_length=255)
    overall: int = Field(..., ge=1, le=99)
    position_ids: list[uuid.UUID] = Field(..., min_length=1)


class PlayerUpdate(_CamelModel):
    """Payload para atualizar um jogador existente."""

    name: str = Field(..., min_length=1, max_length=255)
    overall: int = Field(..., ge=1, le=99)
    position_ids: list[uuid.UUID] = Field(..., min_length=1)
    team_cycle_season_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "TeamCycleSeason do time na temporada atual. Opcional: se omitido, "
            "nao altera o elenco. Se informado e o jogador ja tiver TeamSquad "
            "na temporada atual, atualiza teamCycleSeasonId; senao, cria a linha."
        ),
    )
