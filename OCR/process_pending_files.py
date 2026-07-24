"""
ETL: processa fotos pendentes da tabela File com OCR e grava CSVs no Storage.

Fluxo:
  1. Busca File onde isProcessed = false e parentId IS NULL
  2. Baixa a foto do Supabase Storage
  3. Roda o OCR (main.process_image_to_csv_bytes) -> CSV
  4. Faz upload do CSV no mesmo bucket
  5. Insere um File filho (parentId = id da foto) com metadados + url do CSV
  6. Marca a foto com isProcessed = true

Uso (na pasta OCR, com o venv/deps instalados):
  python process_pending_files.py

Variaveis (reutiliza o .env do back-end):
  DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET
  DB_USE_SSL, DB_SSL_VERIFY (opcionais)
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

import psycopg
import requests
from dotenv import load_dotenv
from psycopg.rows import dict_row
from supabase import Client, create_client

from main import process_image_to_csv_bytes

BASE_DIR = Path(__file__).resolve().parent
BACKEND_ENV = BASE_DIR.parent / "back-end" / ".env"


@dataclass(frozen=True)
class PendingFile:
    file_id: uuid.UUID
    name: str
    url: str
    source_game_id: uuid.UUID | None
    team_cycle_season_id: uuid.UUID | None


def _load_env() -> None:
    if BACKEND_ENV.exists():
        load_dotenv(BACKEND_ENV)
        print(f"[etl] env carregado de: {BACKEND_ENV}")
    else:
        print(f"[etl] aviso: {BACKEND_ENV} nao encontrado")
    load_dotenv(BASE_DIR / ".env", override=True)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")
    return value


def _database_url() -> str:
    raw = _require_env("DATABASE_URL")
    return (
        raw.replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgres://", "postgresql://", 1)
    )


def _connect_db():
    """Abre conexao sync com o Postgres (Supabase), respeitando SSL do .env."""
    conninfo = _database_url()
    use_ssl = os.getenv("DB_USE_SSL", "true").lower() in {"1", "true", "yes"}

    if use_ssl:
        sep = "&" if "?" in conninfo else "?"
        if "sslmode=" not in conninfo.lower():
            conninfo = f"{conninfo}{sep}sslmode=require"

    print("[etl] conectando ao banco...")
    return psycopg.connect(conninfo, row_factory=dict_row)


def _supabase_client() -> Client:
    return create_client(
        _require_env("SUPABASE_URL"),
        _require_env("SUPABASE_SERVICE_ROLE_KEY"),
    )


def _bucket_name() -> str:
    return os.getenv("SUPABASE_STORAGE_BUCKET", "files").strip() or "files"


def fetch_pending_files(conn) -> list[PendingFile]:
    print("[etl] buscando arquivos pendentes (isProcessed=false, parentId IS NULL)...")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id AS file_id,
                name,
                url,
                "sourceGameId" AS source_game_id,
                "teamCycleSeasonId" AS team_cycle_season_id
            FROM "File"
            WHERE "isProcessed" = false
              AND "parentId" IS NULL
            ORDER BY "createdAt" ASC, id ASC
            """
        )
        rows = cur.fetchall()

    pending = [
        PendingFile(
            file_id=row["file_id"],
            name=row["name"],
            url=row["url"],
            source_game_id=row["source_game_id"],
            team_cycle_season_id=row["team_cycle_season_id"],
        )
        for row in rows
    ]
    print(f"[etl] {len(pending)} arquivo(s) pendente(s) encontrado(s)")
    return pending


def object_path_from_public_url(url: str, bucket: str) -> str | None:
    """Extrai o path do objeto a partir da URL publica do Storage."""
    marker = f"/object/public/{bucket}/"
    idx = url.find(marker)
    if idx >= 0:
        return unquote(url[idx + len(marker) :].split("?", 1)[0])

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    try:
        bucket_idx = parts.index(bucket)
        rest = parts[bucket_idx + 1 :]
        if rest:
            return unquote("/".join(rest))
    except ValueError:
        pass
    return None


def download_photo(
    supabase: Client,
    bucket: str,
    file_url: str,
    dest_path: Path,
) -> None:
    """Baixa a foto do bucket (path) ou via URL publica."""
    object_path = object_path_from_public_url(file_url, bucket)
    if object_path:
        print(f"[etl]   baixando do storage: {object_path}")
        content = supabase.storage.from_(bucket).download(object_path)
        dest_path.write_bytes(content)
        return

    print(f"[etl]   baixando via URL publica...")
    response = requests.get(file_url, timeout=120)
    response.raise_for_status()
    dest_path.write_bytes(response.content)


def build_csv_object_path(
    source_game_id: uuid.UUID | None,
    photo_name: str,
) -> str:
    stem = Path(photo_name).stem or "ratings"
    safe_stem = stem.replace("/", "_").replace("\\", "_")
    folder = str(source_game_id) if source_game_id else "unknown-match"
    return f"match-csvs/{folder}/{uuid.uuid4()}_{safe_stem}.csv"


def upload_csv(
    supabase: Client,
    bucket: str,
    object_path: str,
    csv_bytes: bytes,
) -> str:
    print(f"[etl]   enviando CSV para: {object_path}")
    supabase.storage.from_(bucket).upload(
        path=object_path,
        file=csv_bytes,
        file_options={
            "content-type": "text/csv",
            "upsert": "true",
        },
    )
    return supabase.storage.from_(bucket).get_public_url(object_path)


def insert_csv_file(
    conn,
    *,
    parent_id: uuid.UUID,
    name: str,
    url: str,
    source_game_id: uuid.UUID | None,
    team_cycle_season_id: uuid.UUID | None,
) -> uuid.UUID:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO "File" (
                "parentId",
                "sourceGameId",
                "teamCycleSeasonId",
                name,
                extension,
                "mimeType",
                url,
                "isProcessed"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                parent_id,
                source_game_id,
                team_cycle_season_id,
                name,
                "csv",
                "text/csv",
                url,
                False,
            ),
        )
        row = cur.fetchone()
        return row["id"]


def mark_photo_processed(conn, file_id: uuid.UUID) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE "File"
            SET "isProcessed" = true
            WHERE id = %s
            """,
            (file_id,),
        )


def process_one(
    conn,
    supabase: Client,
    bucket: str,
    pending: PendingFile,
    index: int,
    total: int,
) -> None:
    print("")
    print("=" * 60)
    print(f"[etl] ({index}/{total}) fileId={pending.file_id}")
    print(f"[etl]   name={pending.name}")
    print(f"[etl]   sourceGameId={pending.source_game_id}")
    print(f"[etl]   teamCycleSeasonId={pending.team_cycle_season_id}")

    suffix = Path(pending.name).suffix or ".jpg"
    with tempfile.TemporaryDirectory(prefix="fifa-ocr-") as tmp:
        image_path = Path(tmp) / f"photo{suffix}"
        download_photo(supabase, bucket, pending.url, image_path)
        print(f"[etl]   foto salva em: {image_path} ({image_path.stat().st_size} bytes)")

        print("[etl]   rodando OCR...")
        csv_bytes = process_image_to_csv_bytes(str(image_path))
        print(f"[etl]   CSV gerado ({len(csv_bytes)} bytes)")

        object_path = build_csv_object_path(pending.source_game_id, pending.name)
        csv_url = upload_csv(supabase, bucket, object_path, csv_bytes)
        print(f"[etl]   CSV url: {csv_url}")

        csv_file_id = insert_csv_file(
            conn,
            parent_id=pending.file_id,
            name=pending.name,
            url=csv_url,
            source_game_id=pending.source_game_id,
            team_cycle_season_id=pending.team_cycle_season_id,
        )
        print(f"[etl]   File CSV inserido: {csv_file_id} (parentId={pending.file_id})")

        mark_photo_processed(conn, pending.file_id)
        conn.commit()
        print(f"[etl]   foto marcada isProcessed=true")
        print(f"[etl] ({index}/{total}) OK")


def main() -> int:
    print("[etl] iniciando processamento de fotos pendentes")
    _load_env()

    bucket = _bucket_name()
    print(f"[etl] bucket: {bucket}")

    supabase = _supabase_client()
    print("[etl] client Supabase OK")

    ok = 0
    fail = 0

    with _connect_db() as conn:
        print("[etl] banco conectado")
        pending_files = fetch_pending_files(conn)
        if not pending_files:
            print("[etl] nada a processar. Encerrando.")
            return 0

        total = len(pending_files)
        for i, pending in enumerate(pending_files, start=1):
            try:
                process_one(conn, supabase, bucket, pending, i, total)
                ok += 1
            except Exception as exc:
                conn.rollback()
                fail += 1
                print(f"[etl] ERRO em fileId={pending.file_id}: {exc}")
                print("[etl]   rollback feito; seguindo para o proximo")

    print("")
    print("=" * 60)
    print(f"[etl] finalizado | sucesso={ok} | falha={fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[etl] interrompido pelo usuario")
        sys.exit(130)
    except Exception as exc:
        print(f"[etl] falha fatal: {exc}")
        sys.exit(1)
