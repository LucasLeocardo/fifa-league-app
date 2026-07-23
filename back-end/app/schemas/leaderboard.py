"""Schemas Pydantic do leaderboard (artilharia, assistencias e notas)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PlayerGoalsEntry(_CamelModel):
    player_name: str = Field(..., max_length=255)
    team_name: str = Field(..., max_length=255)
    total_goals: int = 0


class PlayerAssistsEntry(_CamelModel):
    player_name: str = Field(..., max_length=255)
    team_name: str = Field(..., max_length=255)
    total_assists: int = 0


class PlayerRatingEntry(_CamelModel):
    player_name: str = Field(..., max_length=255)
    team_name: str = Field(..., max_length=255)
    average_rating: float
    games_played: int = 0


class LeaderboardResponse(_CamelModel):
    """Resposta com as 3 listas do campeonato."""

    cycle_season_id: uuid.UUID
    goals: list[PlayerGoalsEntry]
    assists: list[PlayerAssistsEntry]
    ratings: list[PlayerRatingEntry]
