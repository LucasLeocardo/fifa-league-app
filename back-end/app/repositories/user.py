"""Camada de acesso a dados (repositorio) do User.

Responsabilidade unica: falar com o banco. Trabalha somente com modelos ORM,
sem conhecer schemas Pydantic nem regras de negocio.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.auth_user_id == auth_user_id)
        )
        return result.scalar_one_or_none()

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[User]:
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def save(self, user: User) -> User:
        """Persiste alteracoes de um objeto ja rastreado pela sessao."""
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()
