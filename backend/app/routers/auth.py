from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import (
    LoginRequest,
    SenhaUpdateRequest,
    SetupRequest,
    SetupStatusResponse,
    TokenResponse,
    UsuarioOut,
    UsuarioUpdateRequest,
)
from app.services import auth_service

router = APIRouter()


@router.get("/setup/status", response_model=SetupStatusResponse)
async def obter_status_setup(db: AsyncSession = Depends(get_db)) -> SetupStatusResponse:
    configurado = await auth_service.obter_status(db)
    return SetupStatusResponse(configurado=configurado)


@router.post("/setup", response_model=UsuarioOut, status_code=201)
async def setup(dados: SetupRequest, db: AsyncSession = Depends(get_db)) -> Usuario:
    return await auth_service.realizar_setup(db, dados)


@router.post("/auth/login", response_model=TokenResponse)
async def login(dados: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    token = await auth_service.autenticar(db, dados.email, dados.senha)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UsuarioOut)
async def obter_perfil(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario


@router.put("/auth/me", response_model=UsuarioOut)
async def atualizar_perfil(
    dados: UsuarioUpdateRequest,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    return await auth_service.atualizar_perfil(db, usuario, dados)


@router.put("/auth/me/senha", response_model=UsuarioOut)
async def atualizar_senha(
    dados: SenhaUpdateRequest,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    return await auth_service.atualizar_senha(db, usuario, dados)
