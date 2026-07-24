"""Upload/download de arquivos no Supabase Storage."""

from __future__ import annotations

import uuid
from urllib.parse import quote, unquote, urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import AuthProviderError
from app.core.supabase import get_supabase_admin


def _storage_auth_headers() -> dict[str, str]:
    """Headers com service_role para o Storage (bypassa RLS)."""
    key = settings.supabase_service_role_key
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }


def upload_bytes(
    *,
    content: bytes,
    object_path: str,
    content_type: str,
) -> str:
    """Faz upload no bucket via REST Storage com service_role e retorna URL publica."""
    bucket = settings.supabase_storage_bucket
    encoded_path = quote(object_path, safe="/")
    url = (
        f"{settings.supabase_url.rstrip('/')}"
        f"/storage/v1/object/{bucket}/{encoded_path}"
    )
    headers = {
        **_storage_auth_headers(),
        "Content-Type": content_type or "application/octet-stream",
        "x-upsert": "true",
    }
    try:
        response = httpx.post(url, content=content, headers=headers, timeout=120.0)
        if response.status_code >= 400:
            raise AuthProviderError(
                f"Falha ao enviar arquivo ao Supabase Storage: {response.text}"
            )
        return (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/public/{bucket}/{encoded_path}"
        )
    except AuthProviderError:
        raise
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
    bucket = settings.supabase_storage_bucket
    object_path = object_path_from_public_url(file_url, bucket)

    if object_path:
        encoded_path = quote(object_path, safe="/")
        url = (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/{bucket}/{encoded_path}"
        )
        try:
            response = httpx.get(
                url,
                headers=_storage_auth_headers(),
                timeout=60.0,
                follow_redirects=True,
            )
            if response.is_success and response.content:
                return response.content
        except Exception:
            pass

        try:
            client = get_supabase_admin()
            content = client.storage.from_(bucket).download(object_path)
            if content:
                return content
        except Exception:
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
