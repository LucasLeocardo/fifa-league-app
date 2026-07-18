"""Client Admin do Supabase (service_role) para operacoes de Auth no back-end."""

from functools import lru_cache

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings


@lru_cache
def get_supabase_admin() -> Client:
    """Client com service_role JWT: so usar no servidor, nunca no front."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
