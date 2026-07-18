"""Erros de dominio da aplicacao.

Ficam desacoplados do FastAPI: a camada de servico levanta esses erros e o
main.py os traduz para respostas HTTP (exception handlers). Assim o servico nao
depende de detalhes de HTTP.
"""


class AppError(Exception):
    """Base para todos os erros de dominio."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Recurso solicitado nao existe."""


class ConflictError(AppError):
    """Violacao de regra de unicidade/estado (ex.: email ja cadastrado)."""


class BadRequestError(AppError):
    """Entrada invalida ou rejeitada pelo provedor de Auth."""


class UnauthorizedError(AppError):
    """Credenciais invalidas ou sessao nao autorizada."""


class AuthProviderError(AppError):
    """Falha inesperada no provedor de autenticacao (Supabase Auth)."""
