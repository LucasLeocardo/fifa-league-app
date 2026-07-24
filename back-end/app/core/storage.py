"""Upload de arquivos no Supabase Storage."""

from __future__ import annotations

import uuid

from app.core.config import settings
from app.core.exceptions import AuthProviderError
from app.core.supabase import get_supabase_admin


def upload_bytes(
    *,
    content: bytes,
    object_path: str,
    content_type: str,
) -> str:
    """Faz upload no bucket configurado e retorna a URL publica do arquivo."""
    client = get_supabase_admin()
    bucket = settings.supabase_storage_bucket
    try:
        client.storage.from_(bucket).upload(
            path=object_path,
            file=content,
            file_options={
                "content-type": content_type,
                "upsert": "true",
            },
        )
        return client.storage.from_(bucket).get_public_url(object_path)
    except Exception as exc:
        raise AuthProviderError(
            f"Falha ao enviar arquivo ao Supabase Storage: {exc}"
        ) from exc


def build_match_photo_path(source_game_id: uuid.UUID, file_name: str) -> str:
    """Caminho unico no bucket para fotos de uma partida."""
    safe_name = file_name.replace("/", "_").replace("\\", "_")
    return f"match-photos/{source_game_id}/{uuid.uuid4()}_{safe_name}"
