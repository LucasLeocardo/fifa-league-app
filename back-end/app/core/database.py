"""Engine e sessao assincrona do SQLAlchemy para o Postgres do Supabase."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _build_connect_args() -> dict:
    connect_args: dict = {
        # No pooler transacional (PgBouncer) prepared statements quebram;
        # statement_cache_size=0 desativa o cache do asyncpg.
        "statement_cache_size": settings.db_statement_cache_size,
    }
    if settings.db_use_ssl:
        # Supabase exige SSL; os certificados sao validos (verificacao padrao).
        connect_args["ssl"] = True
    return connect_args


engine = create_async_engine(
    settings.async_database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    connect_args=_build_connect_args(),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia do FastAPI: abre uma sessao por request e fecha ao final."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
