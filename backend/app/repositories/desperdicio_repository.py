from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.desperdicio import Desperdicio
from app.models.material import Material


async def obter_material_para_atualizacao(db: AsyncSession, material_id: int) -> Material | None:
    stmt = select(Material).where(Material.id == material_id).with_for_update()
    resultado = await db.execute(stmt)
    return resultado.scalar_one_or_none()


async def obter_por_id(db: AsyncSession, desperdicio_id: int) -> Desperdicio | None:
    stmt = (
        select(Desperdicio)
        .options(selectinload(Desperdicio.material))
        .where(Desperdicio.id == desperdicio_id)
    )
    resultado = await db.execute(stmt)
    return resultado.scalar_one_or_none()


async def listar(
    db: AsyncSession,
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    material_id: int | None = None,
) -> list[Desperdicio]:
    stmt = select(Desperdicio).options(selectinload(Desperdicio.material))
    if data_inicio is not None:
        stmt = stmt.where(Desperdicio.data >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Desperdicio.data <= data_fim)
    if material_id is not None:
        stmt = stmt.where(Desperdicio.material_id == material_id)

    stmt = stmt.order_by(Desperdicio.data.desc(), Desperdicio.id.desc())
    itens = (await db.execute(stmt)).scalars().all()
    return list(itens)


async def salvar_novo(db: AsyncSession, desperdicio: Desperdicio) -> Desperdicio:
    db.add(desperdicio)
    await db.commit()
    return await obter_por_id(db, desperdicio.id)


async def excluir(db: AsyncSession, desperdicio: Desperdicio) -> None:
    await db.delete(desperdicio)
    await db.commit()
