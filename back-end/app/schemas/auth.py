"""Schemas Pydantic para autenticacao / cadastro / login / refresh."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class RegisterRequest(_CamelModel):
    """Payload de cadastro: cria Auth + registro na tabela User."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(_CamelModel):
    """Payload de login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class LoginResponse(_CamelModel):
    """Resposta de login bem-sucedido."""

    access_token: str
    refresh_token: str
    is_admin: bool


class RefreshRequest(_CamelModel):
    """Payload para renovar a sessao."""

    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(_CamelModel):
    """Nova par de tokens apos o refresh."""

    access_token: str
    refresh_token: str
