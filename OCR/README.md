# OCR — processamento de fotos de partida

Script ETL que busca fotos pendentes na tabela `File`, roda o OCR e grava o CSV correspondente no Supabase Storage.

## Setup e execução

Na pasta `OCR`:

```bash
python -m venv .venv

source .venv/Scripts/activate

./.venv/Scripts/python.exe -m pip install -r requirements.txt

./.venv/Scripts/python.exe process_pending_files.py
```

O script usa as variáveis do `.env` do `back-end` (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`).
