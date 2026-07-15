import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NaoAutorizadoError
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.repositories import usuario_repository as repo

_security_scheme = HTTPBearer(auto_error=False)

MENSAGEM_TOKEN_INVALIDO = "Token de acesso ausente ou inválido"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise NaoAutorizadoError(MENSAGEM_TOKEN_INVALIDO)

    try:
        payload = decodificar_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise NaoAutorizadoError(MENSAGEM_TOKEN_INVALIDO) from exc

    usuario_id = payload.get("sub")
    usuario = await repo.obter_por_id(db, int(usuario_id)) if usuario_id is not None else None
    if usuario is None:
        raise NaoAutorizadoError(MENSAGEM_TOKEN_INVALIDO)
    return usuario
