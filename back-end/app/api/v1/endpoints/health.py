"""Endpoints de saude (liveness e checagem de conexao com o banco)."""

from fastapi import APIRouter, status
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter()


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db", summary="Checa a conexao com o Postgres do Supabase")
async def health_db(db: DbSession) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}


@router.get("/health/ready", status_code=status.HTTP_200_OK, summary="Readiness")
async def readiness(db: DbSession) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}
