"""Schemas Pydantic (contratos de entrada/saida da API) para User.

Usamos alias camelCase para bater com o JSON do front e com o banco, mas os
campos internos ficam em snake_case. populate_by_name=True permite popular tanto
por alias quanto pelo nome do campo.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class UserRead(_CamelModel):
    """Representacao retornada pela API."""

    id: uuid.UUID
    name: str = Field(..., max_length=255)
    email: EmailStr
    coach_name: str | None = Field(default=None, max_length=255)
    auth_user_id: uuid.UUID | None = None
    number_of_titles: int
    is_admin: bool
    created_at: datetime
