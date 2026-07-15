from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    ConflitoError,
    NaoAutorizadoError,
    NaoEncontradoError,
    RequisicaoInvalidaError,
    ValidacaoError,
)
from app.routers import auth, dashboard, desperdicios, materiais, producoes, produtos, relatorios

settings = get_settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PrintFlow API")
app.mount("/api/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(materiais.router, prefix="/api")
app.include_router(produtos.router, prefix="/api")
app.include_router(producoes.router, prefix="/api")
app.include_router(desperdicios.router, prefix="/api")
app.include_router(relatorios.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


_STATUS_POR_EXCECAO: dict[type[AppError], int] = {
    RequisicaoInvalidaError: 400,
    NaoAutorizadoError: 401,
    NaoEncontradoError: 404,
    ConflitoError: 409,
    ValidacaoError: 422,
}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = _STATUS_POR_EXCECAO[type(exc)]
    content = {"detail": exc.detail}
    if isinstance(exc, ValidacaoError):
        content.update(exc.extra)
    return JSONResponse(status_code=status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Dados inválidos", "erros": jsonable_encoder(exc.errors())},
    )
