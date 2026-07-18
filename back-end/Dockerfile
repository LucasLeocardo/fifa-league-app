FROM python:3.12-slim AS base

# Nao gerar .pyc e nao bufferizar stdout/stderr (logs em tempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala dependencias primeiro (melhor uso do cache de camadas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o codigo da aplicacao
COPY app ./app

# Usuario sem privilegios
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
