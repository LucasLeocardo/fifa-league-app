"""Dependencias reutilizaveis dos endpoints (injecao das camadas)."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import get_auth_user_id_from_token
from app.models.user import User
from app.repositories.cycle_season import CycleSeasonRepository
from app.repositories.leaderboard import LeaderboardRepository
from app.repositories.position import PositionRepository
from app.repositories.team_cycle_season import TeamCycleSeasonRepository
from app.repositories.team_squad import TeamSquadRepository
from app.repositories.team_standing import TeamStandingRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.cycle_season import CycleSeasonService
from app.services.leaderboard import LeaderboardService
from app.services.position import PositionService
from app.services.team_cycle_season import TeamCycleSeasonService
from app.services.team_squad import TeamSquadService
from app.services.team_standing import TeamStandingService

# Sessao de banco por request (camada de conexao).
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Bearer JWT enviado pelo front: Authorization: Bearer <access_token>
_bearer = HTTPBearer(auto_error=True)


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_cycle_season_repository(db: DbSession) -> CycleSeasonRepository:
    return CycleSeasonRepository(db)


def get_team_standing_repository(db: DbSession) -> TeamStandingRepository:
    return TeamStandingRepository(db)


def get_team_squad_repository(db: DbSession) -> TeamSquadRepository:
    return TeamSquadRepository(db)


def get_team_cycle_season_repository(
    db: DbSession,
) -> TeamCycleSeasonRepository:
    return TeamCycleSeasonRepository(db)


def get_cycle_season_service(
    repository: Annotated[
        CycleSeasonRepository, Depends(get_cycle_season_repository)
    ],
) -> CycleSeasonService:
    return CycleSeasonService(repository)


def get_team_squad_service(
    repository: Annotated[
        TeamSquadRepository, Depends(get_team_squad_repository)
    ],
) -> TeamSquadService:
    return TeamSquadService(repository)


def get_team_cycle_season_service(
    repository: Annotated[
        TeamCycleSeasonRepository, Depends(get_team_cycle_season_repository)
    ],
) -> TeamCycleSeasonService:
    return TeamCycleSeasonService(repository)


def get_position_repository(db: DbSession) -> PositionRepository:
    return PositionRepository(db)


def get_position_service(
    repository: Annotated[PositionRepository, Depends(get_position_repository)],
) -> PositionService:
    return PositionService(repository)


def get_leaderboard_repository(db: DbSession) -> LeaderboardRepository:
    return LeaderboardRepository(db)


def get_leaderboard_service(
    leaderboard_repository: Annotated[
        LeaderboardRepository, Depends(get_leaderboard_repository)
    ],
    cycle_season_repository: Annotated[
        CycleSeasonRepository, Depends(get_cycle_season_repository)
    ],
) -> LeaderboardService:
    return LeaderboardService(leaderboard_repository, cycle_season_repository)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repository)


def get_team_standing_service(
    standing_repository: Annotated[
        TeamStandingRepository, Depends(get_team_standing_repository)
    ],
    cycle_season_repository: Annotated[
        CycleSeasonRepository, Depends(get_cycle_season_repository)
    ],
) -> TeamStandingService:
    return TeamStandingService(standing_repository, cycle_season_repository)


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
CycleSeasonServiceDep = Annotated[
    CycleSeasonService, Depends(get_cycle_season_service)
]
TeamStandingServiceDep = Annotated[
    TeamStandingService, Depends(get_team_standing_service)
]
TeamSquadServiceDep = Annotated[
    TeamSquadService, Depends(get_team_squad_service)
]
TeamCycleSeasonServiceDep = Annotated[
    TeamCycleSeasonService, Depends(get_team_cycle_season_service)
]
LeaderboardServiceDep = Annotated[
    LeaderboardService, Depends(get_leaderboard_service)
]
PositionServiceDep = Annotated[PositionService, Depends(get_position_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
BearerTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]
