"""Agrega todos os routers da versao 1 da API."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    cycle_seasons,
    health,
    leaderboard,
    match_types,
    matches,
    positions,
    squad,
    standings,
    team_cycle_seasons,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(standings.router, prefix="/standings", tags=["standings"])
api_router.include_router(
    cycle_seasons.router, prefix="/cycle-seasons", tags=["cycle-seasons"]
)
api_router.include_router(squad.router, prefix="/squad", tags=["squad"])
api_router.include_router(
    team_cycle_seasons.router,
    prefix="/team-cycle-seasons",
    tags=["team-cycle-seasons"],
)
api_router.include_router(
    leaderboard.router, prefix="/leaderboard", tags=["leaderboard"]
)
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(
    match_types.router, prefix="/match-types", tags=["match-types"]
)
