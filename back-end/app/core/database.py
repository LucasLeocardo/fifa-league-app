"""Engine e sessao assincrona do SQLAlchemy para o Postgres do Supabase."""

import ssl
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _build_ssl_arg() -> bool | ssl.SSLContext:
    """Monta o argumento SSL do asyncpg.

    Supabase exige TLS. Se db_ssl_verify=False (ex.: proxy corporativo com
    certificado autoassinado), ainda usa SSL, mas sem validar a cadeia.
    """
    if settings.db_ssl_verify:
        return True
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _build_connect_args() -> dict:
    # Supabase usa PgBouncer em modo transaction: prepared statements
    # nomeados nao sobrevivem entre round-trips (a conexao de backend
    # muda). Desligar os dois caches e usar nomes unicos evita
    # DuplicatePreparedStatementError e InvalidSQLStatementNameError.
    connect_args: dict = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    }
    if settings.db_use_ssl:
        connect_args["ssl"] = _build_ssl_arg()
    return connect_args


engine = create_async_engine(
    settings.async_database_url,
    echo=settings.db_echo,
    poolclass=NullPool,
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
