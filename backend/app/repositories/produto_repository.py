from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.produto import Produto
from app.models.produto_material import ProdutoMaterial

_CARREGAR_COMPOSICAO = selectinload(Produto.composicao).selectinload(ProdutoMaterial.material)


async def obter_por_id(db: AsyncSession, produto_id: int) -> Produto | None:
    stmt = select(Produto).options(_CARREGAR_COMPOSICAO).where(Produto.id == produto_id)
    resultado = await db.execute(stmt)
    return resultado.scalar_one_or_none()


async def existe_nome_ativo(db: AsyncSession, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Produto.id).where(Produto.nome == nome, Produto.ativo.is_(True))
    if ignorar_id is not None:
        stmt = stmt.where(Produto.id != ignorar_id)
    resultado = await db.execute(stmt)
    return resultado.first() is not None


async def listar(
    db: AsyncSession,
    *,
    ativo: bool | None = None,
    busca: str | None = None,
) -> list[Produto]:
    stmt = select(Produto).options(_CARREGAR_COMPOSICAO)
    if ativo is not None:
        stmt = stmt.where(Produto.ativo.is_(ativo))
    if busca:
        stmt = stmt.where(Produto.nome.ilike(f"%{busca}%"))

    stmt = stmt.order_by(Produto.nome)
    itens = (await db.execute(stmt)).scalars().all()
    return list(itens)


async def criar(db: AsyncSession, produto: Produto) -> Produto:
    db.add(produto)
    await db.commit()
    return await obter_por_id(db, produto.id)


async def salvar(db: AsyncSession, produto: Produto) -> Produto:
    await db.commit()
    return await obter_por_id(db, produto.id)


async def excluir(db: AsyncSession, produto: Produto) -> None:
    await db.delete(produto)
    await db.commit()
