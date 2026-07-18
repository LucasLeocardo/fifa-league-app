"""Agrega todos os routers da versao 1 da API."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, standings

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(standings.router, prefix="/standings", tags=["standings"])
