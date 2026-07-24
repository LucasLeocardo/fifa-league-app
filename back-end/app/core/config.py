"""Configuracao da aplicacao, carregada de variaveis de ambiente (.env)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # Em redes corporativas (proxy/MITM) a validacao do certificado pode falhar.
    # Em producao mantenha True.
    db_ssl_verify: bool = True
    # 0 = desativa prepared statements (necessario no pooler transacional 6543).
    db_statement_cache_size: int = 0

    # --- Supabase Auth (Admin API; service_role JWT so no back-end) ---
    supabase_url: str = Field(
        ...,
        description="URL do projeto Supabase (ex.: https://xxxx.supabase.co)",
    )
    supabase_service_role_key: str = Field(
        ...,
        description="Service role key JWT do Supabase (eyJ...; nunca expor no front)",
    )
    supabase_storage_bucket: str = Field(
        default="files",
        description="Nome do bucket no Supabase Storage para upload de fotos",
    )

    # --- CORS ---
    # NoDecode: evita json.loads automatico do EnvSettingsSource (quebra CSV no Railway).
    # Aceita JSON (["https://a.com"]) ou CSV (https://a.com,http://localhost:3000).
    backend_cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000"
    ]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                parsed = json.loads(text)
                if not isinstance(parsed, list):
                    raise ValueError(
                        "BACKEND_CORS_ORIGINS JSON precisa ser uma lista."
                    )
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

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
