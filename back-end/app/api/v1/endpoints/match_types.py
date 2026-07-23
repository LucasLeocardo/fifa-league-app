"""Camada de rotas de MatchType."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, MatchTypeServiceDep
from app.schemas.match_type import MatchTypeRead

router = APIRouter()


@router.get(
    "",
    summary="Lista todos os MatchTypes (matchTypeId e name)",
)
async def list_match_types(
    service: MatchTypeServiceDep,
    _current_user: CurrentUserDep,
) -> list[MatchTypeRead]:
    """Retorna matchTypeId e name de todas as linhas da tabela MatchType."""
    return await service.list_all()
