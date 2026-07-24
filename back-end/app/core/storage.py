"""Upload/download de arquivos no Supabase Storage."""

from __future__ import annotations

import uuid
from urllib.parse import unquote, urlparse

import httpx

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


def object_path_from_public_url(url: str, bucket: str | None = None) -> str | None:
    """Extrai o path do objeto a partir da URL publica do Storage."""
    bucket_name = bucket or settings.supabase_storage_bucket
    marker = f"/object/public/{bucket_name}/"
    idx = url.find(marker)
    if idx >= 0:
        return unquote(url[idx + len(marker) :].split("?", 1)[0])

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    try:
        bucket_idx = parts.index(bucket_name)
        rest = parts[bucket_idx + 1 :]
        if rest:
            return unquote("/".join(rest))
    except ValueError:
        pass
    return None


def download_bytes(*, file_url: str) -> bytes:
    """Baixa o conteudo do arquivo pela URL (Storage path ou URL publica)."""
    client = get_supabase_admin()
    bucket = settings.supabase_storage_bucket
    object_path = object_path_from_public_url(file_url, bucket)

    try:
        if object_path:
            content = client.storage.from_(bucket).download(object_path)
            if content:
                return content
    except Exception:
        # Cai para download HTTP pela URL publica.
        pass

    try:
        response = httpx.get(file_url, timeout=60.0, follow_redirects=True)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        raise AuthProviderError(
            f"Falha ao baixar arquivo do Storage: {exc}"
        ) from exc


def build_match_photo_path(source_game_id: uuid.UUID, file_name: str) -> str:
    """Caminho unico no bucket para fotos de uma partida."""
    safe_name = file_name.replace("/", "_").replace("\\", "_")
    return f"match-photos/{source_game_id}/{uuid.uuid4()}_{safe_name}"
