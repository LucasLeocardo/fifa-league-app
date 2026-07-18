"""Ponto de entrada da aplicacao FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    AuthProviderError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nada obrigatorio aqui (o schema ja existe no Supabase).
    yield
    # Shutdown: encerra o pool de conexoes de forma limpa.
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    if settings.backend_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.backend_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    _register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["root"], summary="Info da API")
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "environment": settings.environment,
            "docs": "/docs",
        }

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Traduz erros de dominio (camada de servico) em respostas HTTP."""

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message}
        )

    @app.exception_handler(ConflictError)
    async def _handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message}
        )

    @app.exception_handler(BadRequestError)
    async def _handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message}
        )

    @app.exception_handler(UnauthorizedError)
    async def _handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": exc.message}
        )

    @app.exception_handler(AuthProviderError)
    async def _handle_auth_provider(_: Request, exc: AuthProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": exc.message}
        )


app = create_app()
