"""Camada de rotas de autenticacao: apenas HTTP (delega ao AuthService)."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, BearerTokenDep
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)
from app.schemas.user import UserRead

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Ativa conta Auth para um User pre-cadastrado",
)
async def register(payload: RegisterRequest, service: AuthServiceDep) -> UserRead:
    """Vincula Auth a um registro User ja existente (email autorizado).

    Exige que o email exista na tabela User com authUserId vazio. Cria o
    usuario no Supabase Auth, preenche authUserId e envia confirmacao de email.
    """
    return await service.register(payload)


@router.post(
    "/login",
    summary="Autentica um usuario e retorna os tokens",
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> LoginResponse:
    """Valida email/senha no Supabase Auth e confere a existencia na tabela User.

    Em sucesso, retorna accessToken, refreshToken, isAdmin, name e coachName.
    O front deve enviar o accessToken no header Authorization: Bearer nas rotas
    protegidas e guardar o refreshToken para renovar a sessao.
    """
    return await service.login(payload)


@router.post(
    "/refresh",
    summary="Renova access e refresh tokens",
)
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> RefreshResponse:
    """Troca o refreshToken por um novo par de tokens.

    O refreshToken antigo deixa de valer (uso unico). O front deve substituir
    ambos os tokens pelos valores retornados.
    """
    return await service.refresh(payload)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerra a sessao atual",
)
async def logout(credentials: BearerTokenDep, service: AuthServiceDep) -> None:
    """Revoga a sessao no Supabase Auth (scope local = este dispositivo).

    Envie Authorization: Bearer <accessToken>. Depois, o front deve apagar
    accessToken e refreshToken do storage local.
    """
    await service.logout(credentials.credentials)
