"""Camada de rotas de Position."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, PositionServiceDep
from app.schemas.position import PositionRead

router = APIRouter()


@router.get(
    "",
    summary="Lista todas as posicoes (id e code)",
)
async def list_positions(
    service: PositionServiceDep,
    _current_user: CurrentUserDep,
) -> list[PositionRead]:
    """Retorna id e code de todas as linhas da tabela Position."""
    return await service.list_all()
