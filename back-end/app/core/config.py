"""Configuracao da aplicacao, carregada de variaveis de ambiente (.env)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicacao ---
    app_name: str = "FIFA League API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Banco de dados (Supabase Postgres) ---
    database_url: str = Field(
        ...,
        description="Ex.: postgresql+asyncpg://postgres:senha@host:5432/postgres",
    )
    db_echo: bool = False
    db_use_ssl: bool = True
    # 0 = desativa prepared statements (necessario no pooler transacional 6543).
    db_statement_cache_size: int = 0

    # --- Supabase Auth (Admin API; secret key so no back-end) ---
    supabase_url: str = Field(
        ...,
        description="URL do projeto Supabase (ex.: https://xxxx.supabase.co)",
    )
    supabase_secret_key: str = Field(
        ...,
        description="Secret key do Supabase (sb_secret_...; nunca expor no front)",
    )

    # --- CORS ---
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def async_database_url(self) -> str:
        """Garante o driver asyncpg mesmo se a URL vier no formato padrao."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Retorna as configuracoes (cacheadas) para uso via injecao de dependencia."""
    return Settings()


settings = get_settings()
