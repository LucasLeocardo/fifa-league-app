"""Camada de servico de autenticacao (cadastro, login e refresh via Supabase)."""

from __future__ import annotations

import logging
import uuid

from gotrue.errors import AuthApiError

from app.core.exceptions import (
    AuthProviderError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.supabase import get_supabase_admin
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)

logger = logging.getLogger(__name__)


def _attr(obj: object | None, name: str) -> object | None:
    """Le atributo de objeto ou chave de dict; None se obj for None."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _user_id(user: object | None) -> object | None:
    """Extrai o id do user (objeto ou dict)."""
    return _attr(user, "id")


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
        self._supabase = get_supabase_admin()

    async def register(self, data: RegisterRequest) -> User:
        """Ativa conta Auth para um User ja pre-cadastrado no banco.

        So permite cadastro se o email existir na tabela User e o authUserId
        ainda estiver vazio. Cria o usuario no Supabase Auth, vincula o
        authUserId e envia o email de confirmacao.
        """
        user = await self.repository.get_by_email(str(data.email))
        if user is None:
            raise NotFoundError("Email nao autorizado para cadastro.")
        if user.auth_user_id is not None:
            raise ConflictError("Este email ja possui uma conta ativa.")

        auth_user_id = self._create_auth_user(data)

        try:
            # create_user Admin nao envia o email; reenvia o de confirmacao.
            self._send_confirmation_email(str(data.email))
        except Exception:
            logger.exception(
                "Falha ao enviar email de confirmacao para %s", data.email
            )

        user.auth_user_id = auth_user_id
        user.name = data.name
        try:
            return await self.repository.save(user)
        except Exception:
            self._delete_auth_user(auth_user_id)
            raise

    async def login(self, data: LoginRequest) -> LoginResponse:
        """Autentica no Supabase Auth e confirma que o User existe no banco."""
        auth_user_id, access_token, refresh_token = self._sign_in(data)

        user = await self.repository.get_by_auth_user_id(auth_user_id)
        if user is None:
            raise NotFoundError("Usuario autenticado nao encontrado no aplicativo.")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            is_admin=user.is_admin,
            name=user.name,
            coach_name=user.coach_name,
            number_of_titles=user.number_of_titles,
        )

    async def refresh(self, data: RefreshRequest) -> RefreshResponse:
        """Troca o refresh token por um novo par access/refresh.

        Refresh tokens do Supabase sao de uso unico: o front deve substituir o
        refreshToken antigo pelo novo retornado aqui.
        """
        access_token, refresh_token, auth_user_id = self._refresh_session(
            data.refresh_token
        )

        user = await self.repository.get_by_auth_user_id(auth_user_id)
        if user is None:
            raise UnauthorizedError("Usuario do token nao encontrado no aplicativo.")

        return RefreshResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def logout(self, access_token: str) -> None:
        """Encerra a sessao atual no Supabase Auth (scope local).

        Revoga o refresh token da sessao. O access token JWT ainda pode valer
        ate o `exp`; o front deve apagar accessToken e refreshToken localmente.
        """
        try:
            self._supabase.auth.admin.sign_out(access_token, scope="local")
        except AuthApiError as exc:
            message = (exc.message or str(exc)).lower()
            if (
                "invalid" in message
                or "expired" in message
                or (exc.status is not None and exc.status in {400, 401})
            ):
                raise UnauthorizedError("Token invalido ou expirado.") from exc
            if exc.status is not None and 400 <= exc.status < 500:
                raise BadRequestError(exc.message or "Falha ao encerrar a sessao.") from exc
            raise AuthProviderError(exc.message or "Falha ao encerrar a sessao.") from exc
        except Exception as exc:
            raise AuthProviderError("Falha ao encerrar a sessao.") from exc

    def _sign_in(self, data: LoginRequest) -> tuple[uuid.UUID, str, str]:
        try:
            response = self._supabase.auth.sign_in_with_password(
                {
                    "email": str(data.email),
                    "password": data.password,
                }
            )
        except AuthApiError as exc:
            message = (exc.message or str(exc)).lower()
            if (
                "invalid" in message
                or "credentials" in message
                or "email not confirmed" in message
                or (exc.status is not None and exc.status in {400, 401})
            ):
                raise UnauthorizedError("Credenciais invalidas.") from exc
            if exc.status is not None and 400 <= exc.status < 500:
                raise BadRequestError(exc.message or "Falha no login.") from exc
            raise AuthProviderError(exc.message or "Falha ao autenticar.") from exc
        except Exception as exc:
            raise AuthProviderError("Falha ao autenticar.") from exc

        return self._extract_session_tokens(response)

    def _refresh_session(self, refresh_token: str) -> tuple[str, str, uuid.UUID]:
        try:
            response = self._supabase.auth.refresh_session(refresh_token)
        except AuthApiError as exc:
            message = (exc.message or str(exc)).lower()
            if (
                "invalid" in message
                or "expired" in message
                or "already used" in message
                or (exc.status is not None and exc.status in {400, 401})
            ):
                raise UnauthorizedError("Refresh token invalido ou expirado.") from exc
            if exc.status is not None and 400 <= exc.status < 500:
                raise BadRequestError(exc.message or "Falha ao renovar o token.") from exc
            raise AuthProviderError(exc.message or "Falha ao renovar o token.") from exc
        except Exception as exc:
            raise AuthProviderError("Falha ao renovar o token.") from exc

        auth_user_id, access_token, new_refresh = self._extract_session_tokens(response)
        return access_token, new_refresh, auth_user_id

    def _extract_session_tokens(
        self, response: object
    ) -> tuple[uuid.UUID, str, str]:
        session = _attr(response, "session")
        user_id = _user_id(_attr(response, "user")) or _user_id(_attr(session, "user"))
        access_token = _attr(session, "access_token")
        refresh_token = _attr(session, "refresh_token")

        if not user_id:
            raise AuthProviderError("Supabase Auth nao retornou o id do usuario.")
        if not access_token:
            raise AuthProviderError("Supabase Auth nao retornou o access token.")
        if not refresh_token:
            raise AuthProviderError("Supabase Auth nao retornou o refresh token.")

        return uuid.UUID(str(user_id)), str(access_token), str(refresh_token)

    def _create_auth_user(self, data: RegisterRequest) -> uuid.UUID:
        try:
            response = self._supabase.auth.admin.create_user(
                {
                    "email": str(data.email),
                    "password": data.password,
                    "email_confirm": False,
                    "user_metadata": {"name": data.name},
                }
            )
        except AuthApiError as exc:
            message = (exc.message or str(exc)).lower()
            if "already" in message or "registered" in message or "exists" in message:
                raise ConflictError("Ja existe um usuario com esse email.") from exc
            if exc.status is not None and 400 <= exc.status < 500:
                raise BadRequestError(exc.message or "Dados de cadastro invalidos.") from exc
            raise AuthProviderError(
                exc.message or "Falha ao criar usuario no Auth."
            ) from exc
        except Exception as exc:
            raise AuthProviderError("Falha ao criar usuario no Auth.") from exc

        user = getattr(response, "user", None) or response
        user_id = getattr(user, "id", None)
        if user_id is None and isinstance(user, dict):
            user_id = user.get("id")
        if not user_id:
            raise AuthProviderError("Supabase Auth nao retornou o id do usuario.")
        return uuid.UUID(str(user_id))

    def _send_confirmation_email(self, email: str) -> None:
        self._supabase.auth.resend({"type": "signup", "email": email})

    def _delete_auth_user(self, auth_user_id: uuid.UUID) -> None:
        try:
            self._supabase.auth.admin.delete_user(str(auth_user_id))
        except Exception:
            logger.exception(
                "Falha ao compensar: nao foi possivel apagar Auth user %s",
                auth_user_id,
            )
