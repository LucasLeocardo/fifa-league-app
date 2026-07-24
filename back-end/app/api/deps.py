"""Dependencias reutilizaveis dos endpoints (injecao das camadas)."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import get_auth_user_id_from_token
from app.models.user import User
from app.repositories.cycle_season import CycleSeasonRepository
from app.repositories.file import FileRepository
from app.repositories.leaderboard import LeaderboardRepository
from app.repositories.match import MatchRepository
from app.repositories.match_player_stat import MatchPlayerStatRepository
from app.repositories.match_type import MatchTypeRepository
from app.repositories.player import PlayerRepository
from app.repositories.position import PositionRepository
from app.repositories.team_cycle_season import TeamCycleSeasonRepository
from app.repositories.team_squad import TeamSquadRepository
from app.repositories.team_standing import TeamStandingRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.cycle_season import CycleSeasonService
from app.services.file import FileService
from app.services.leaderboard import LeaderboardService
from app.services.match import MatchService
from app.services.match_player_stat import MatchPlayerStatService
from app.services.match_type import MatchTypeService
from app.services.player import PlayerService
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


def get_match_type_repository(db: DbSession) -> MatchTypeRepository:
    return MatchTypeRepository(db)


def get_match_type_service(
    repository: Annotated[
        MatchTypeRepository, Depends(get_match_type_repository)
    ],
) -> MatchTypeService:
    return MatchTypeService(repository)


def get_match_repository(db: DbSession) -> MatchRepository:
    return MatchRepository(db)


def get_match_service(
    repository: Annotated[MatchRepository, Depends(get_match_repository)],
) -> MatchService:
    return MatchService(repository)


def get_player_repository(db: DbSession) -> PlayerRepository:
    return PlayerRepository(db)


def get_player_service(
    repository: Annotated[PlayerRepository, Depends(get_player_repository)],
) -> PlayerService:
    return PlayerService(repository)


def get_file_repository(db: DbSession) -> FileRepository:
    return FileRepository(db)


def get_file_service(
    db: DbSession,
    repository: Annotated[FileRepository, Depends(get_file_repository)],
) -> FileService:
    return FileService(db, repository)


def get_match_player_stat_repository(db: DbSession) -> MatchPlayerStatRepository:
    return MatchPlayerStatRepository(db)


def get_match_player_stat_service(
    db: DbSession,
    player_repository: Annotated[
        PlayerRepository, Depends(get_player_repository)
    ],
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    match_player_stat_repository: Annotated[
        MatchPlayerStatRepository, Depends(get_match_player_stat_repository)
    ],
) -> MatchPlayerStatService:
    return MatchPlayerStatService(
        db,
        player_repository,
        file_repository,
        match_player_stat_repository,
    )


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


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Exige usuario autenticado com isAdmin = true."""
    if not current_user.is_admin:
        raise ForbiddenError("Apenas administradores podem realizar esta operacao.")
    return current_user


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
MatchServiceDep = Annotated[MatchService, Depends(get_match_service)]
MatchTypeServiceDep = Annotated[
    MatchTypeService, Depends(get_match_type_service)
]
PlayerServiceDep = Annotated[PlayerService, Depends(get_player_service)]
FileServiceDep = Annotated[FileService, Depends(get_file_service)]
MatchPlayerStatServiceDep = Annotated[
    MatchPlayerStatService, Depends(get_match_player_stat_service)
]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminUserDep = Annotated[User, Depends(get_current_admin_user)]
BearerTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]
