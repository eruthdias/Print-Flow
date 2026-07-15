class AppError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class RequisicaoInvalidaError(AppError):
    """400 — requisição semanticamente inválida (ex: senha atual incorreta)."""


class NaoAutorizadoError(AppError):
    """401 — autenticação ausente ou inválida."""


class NaoEncontradoError(AppError):
    """404 — recurso não encontrado."""


class ConflitoError(AppError):
    """409 — conflito de estado (duplicidade, vínculos existentes)."""


class ValidacaoError(AppError):
    """422 — violação de regra de negócio. Aceita payload extra para o corpo da resposta."""

    def __init__(self, detail: str, **extra):
        super().__init__(detail)
        self.extra = extra
