"""Client Admin do Supabase (secret key) para operacoes de Auth no back-end."""

from functools import lru_cache

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings


@lru_cache
def get_supabase_admin() -> Client:
    """Client com secret key: so usar no servidor, nunca no front."""
    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
