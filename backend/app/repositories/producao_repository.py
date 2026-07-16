from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import Material
from app.models.desperdicio import Desperdicio
from app.models.producao import Producao
from app.models.producao_item import ProducaoItem

_CARREGAR_DETALHE = (
    selectinload(Producao.produto),
    selectinload(Producao.itens).selectinload(ProducaoItem.material),
    selectinload(Producao.desperdicios).selectinload(Desperdicio.material),
)


async def obter_materiais_para_atualizacao(
    db: AsyncSession, material_ids: list[int]
) -> dict[int, Material]:
    stmt = select(Material).where(Material.id.in_(material_ids)).with_for_update()
    resultado = await db.execute(stmt)
    return {material.id: material for material in resultado.scalars().all()}


async def obter_por_id(db: AsyncSession, producao_id: int) -> Producao | None:
    stmt = select(Producao).options(*_CARREGAR_DETALHE).where(Producao.id == producao_id)
    resultado = await db.execute(stmt)
    return resultado.scalar_one_or_none()


async def listar(
    db: AsyncSession,
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    produto_id: int | None = None,
) -> list[Producao]:
    stmt = select(Producao).options(*_CARREGAR_DETALHE)
    if data_inicio is not None:
        stmt = stmt.where(Producao.data_producao >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Producao.data_producao <= data_fim)
    if produto_id is not None:
        stmt = stmt.where(Producao.produto_id == produto_id)

    stmt = stmt.order_by(Producao.data_producao.desc(), Producao.id.desc())
    itens = (await db.execute(stmt)).scalars().all()
    return list(itens)


async def salvar_novo(db: AsyncSession, producao: Producao) -> Producao:
    db.add(producao)
    await db.commit()
    return await obter_por_id(db, producao.id)


async def excluir(db: AsyncSession, producao: Producao) -> None:
    await db.delete(producao)
    await db.commit()
