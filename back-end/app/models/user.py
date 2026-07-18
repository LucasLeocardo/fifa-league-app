"""Modelo ORM da tabela "User" (mapeada ao schema criado no Supabase).

Importante: no banco os identificadores usam PascalCase/camelCase (ex.: "User",
"authUserId", "numberOfTitles", "createdAt"). Aqui usamos nomes Pythonicos
(snake_case) nos atributos e mapeamos explicitamente para o nome real da coluna
no primeiro argumento de mapped_column(...).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "User"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    auth_user_id: Mapped[uuid.UUID | None] = mapped_column(
        "authUserId",
        UUID(as_uuid=True),
        unique=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    email: Mapped[str] = mapped_column("email", String(255), nullable=False)
    coach_name: Mapped[str | None] = mapped_column(
        "coachName", String(255), nullable=True
    )
    number_of_titles: Mapped[int] = mapped_column(
        "numberOfTitles",
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    is_admin: Mapped[bool] = mapped_column(
        "isAdmin",
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
