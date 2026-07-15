from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflitoError, NaoAutorizadoError, RequisicaoInvalidaError
from app.core.security import criar_token, hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.repositories import usuario_repository as repo
from app.schemas.usuario import SenhaUpdateRequest, SetupRequest, UsuarioUpdateRequest

MENSAGEM_LOGIN_INVALIDO = "Email ou senha inválidos"


async def obter_status(db: AsyncSession) -> bool:
    return await repo.contar(db) > 0


async def realizar_setup(db: AsyncSession, dados: SetupRequest) -> Usuario:
    if await repo.contar(db) > 0:
        raise ConflitoError("Administrador já configurado")
    usuario = Usuario(nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha))
    return await repo.criar(db, usuario)


async def autenticar(db: AsyncSession, email: str, senha: str) -> str:
    usuario = await repo.obter_por_email(db, email)
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        raise NaoAutorizadoError(MENSAGEM_LOGIN_INVALIDO)
    return criar_token(str(usuario.id))


async def atualizar_perfil(db: AsyncSession, usuario: Usuario, dados: UsuarioUpdateRequest) -> Usuario:
    usuario.nome = dados.nome
    usuario.email = dados.email
    return await repo.salvar(db, usuario)


async def atualizar_senha(db: AsyncSession, usuario: Usuario, dados: SenhaUpdateRequest) -> Usuario:
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise RequisicaoInvalidaError("Senha atual incorreta")
    usuario.senha_hash = hash_senha(dados.senha_nova)
    return await repo.salvar(db, usuario)
