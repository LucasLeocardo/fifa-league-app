"""Utilitarios de seguranca: validacao de JWT do Supabase Auth."""

from __future__ import annotations

import uuid

from gotrue.errors import AuthApiError

from app.core.exceptions import AuthProviderError, UnauthorizedError
from app.core.supabase import get_supabase_admin


def get_auth_user_id_from_token(access_token: str) -> uuid.UUID:
    """Valida o access token JWT no Supabase Auth e devolve o auth user id (`sub`)."""
    try:
        response = get_supabase_admin().auth.get_user(access_token)
    except AuthApiError as exc:
        raise UnauthorizedError("Token invalido ou expirado.") from exc
    except Exception as exc:
        raise AuthProviderError("Falha ao validar o token.") from exc

    user = getattr(response, "user", None)
    user_id = getattr(user, "id", None) if user is not None else None
    if user_id is None and isinstance(user, dict):
        user_id = user.get("id")
    if not user_id:
        raise UnauthorizedError("Token invalido ou expirado.")
    return uuid.UUID(str(user_id))
