from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario


async def contar(db: AsyncSession) -> int:
    resultado = await db.execute(select(func.count()).select_from(Usuario))
    return resultado.scalar_one()


async def obter_por_email(db: AsyncSession, email: str) -> Usuario | None:
    resultado = await db.execute(select(Usuario).where(Usuario.email == email))
    return resultado.scalar_one_or_none()


async def obter_por_id(db: AsyncSession, usuario_id: int) -> Usuario | None:
    return await db.get(Usuario, usuario_id)


async def criar(db: AsyncSession, usuario: Usuario) -> Usuario:
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def salvar(db: AsyncSession, usuario: Usuario) -> Usuario:
    await db.commit()
    await db.refresh(usuario)
    return usuario
