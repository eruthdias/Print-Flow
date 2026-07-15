from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.desperdicio import Desperdicio
from app.models.material import Material
from app.models.produto import Produto


async def obter_por_id(db: AsyncSession, material_id: int) -> Material | None:
    return await db.get(Material, material_id)


async def existe_nome_ativo(db: AsyncSession, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Material.id).where(Material.nome == nome, Material.ativo.is_(True))
    if ignorar_id is not None:
        stmt = stmt.where(Material.id != ignorar_id)
    resultado = await db.execute(stmt)
    return resultado.first() is not None


async def listar(
    db: AsyncSession,
    *,
    ativo: bool | None = None,
    estoque_baixo: bool | None = None,
    busca: str | None = None,
) -> list[Material]:
    stmt = select(Material)
    if ativo is not None:
        stmt = stmt.where(Material.ativo.is_(ativo))
    if estoque_baixo:
        stmt = stmt.where(Material.quantidade_atual < Material.quantidade_minima)
    if busca:
        stmt = stmt.where(Material.nome.ilike(f"%{busca}%"))

    stmt = stmt.order_by(Material.nome)
    itens = (await db.execute(stmt)).scalars().all()
    return list(itens)


async def obter_resumo(db: AsyncSession) -> tuple[int, int, int, int, int, int]:
    materiais_cadastrados = (
        select(func.count())
        .select_from(Material)
        .where(Material.ativo.is_(True))
        .scalar_subquery()
    )
    materiais_em_estoque = (
        select(func.count())
        .select_from(Material)
        .where(Material.ativo.is_(True), Material.quantidade_atual > 0)
        .scalar_subquery()
    )
    materiais_sem_estoque = (
        select(func.count())
        .select_from(Material)
        .where(Material.ativo.is_(True), Material.quantidade_atual == 0)
        .scalar_subquery()
    )
    produtos_cadastrados = (
        select(func.count())
        .select_from(Produto)
        .where(Produto.ativo.is_(True))
        .scalar_subquery()
    )
    desperdicios_registrados = select(func.count()).select_from(Desperdicio).scalar_subquery()
    precisando_compra = (
        select(func.count())
        .select_from(Material)
        .where(
            Material.ativo.is_(True),
            Material.quantidade_atual < Material.quantidade_minima,
        )
        .scalar_subquery()
    )

    stmt = select(
        materiais_cadastrados,
        materiais_em_estoque,
        materiais_sem_estoque,
        produtos_cadastrados,
        desperdicios_registrados,
        precisando_compra,
    )
    return tuple((await db.execute(stmt)).one())


async def criar(db: AsyncSession, material: Material) -> Material:
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


async def salvar(db: AsyncSession, material: Material) -> Material:
    await db.commit()
    await db.refresh(material)
    return material


async def excluir(db: AsyncSession, material: Material) -> None:
    await db.delete(material)
    await db.commit()
