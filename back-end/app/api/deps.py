"""Dependencias reutilizaveis dos endpoints (injecao das camadas)."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import get_auth_user_id_from_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService

# Sessao de banco por request (camada de conexao).
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Bearer JWT enviado pelo front: Authorization: Bearer <access_token>
_bearer = HTTPBearer(auto_error=True)


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repository)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Exige JWT valido e um registro correspondente na tabela User.

    Use `CurrentUserDep` nos endpoints protegidos. Rotas publicas (health,
    auth/register, auth/login) nao devem depender disso.
    """
    auth_user_id = get_auth_user_id_from_token(credentials.credentials)
    user = await repository.get_by_auth_user_id(auth_user_id)
    if user is None:
        raise UnauthorizedError("Usuario do token nao encontrado no aplicativo.")
    return user


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
BearerTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]
