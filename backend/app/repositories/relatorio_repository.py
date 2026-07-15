from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.desperdicio import Desperdicio
from app.models.material import Material
from app.models.producao import Producao
from app.models.producao_item import ProducaoItem
from app.models.produto import Produto


async def obter_estoque_atual(db: AsyncSession) -> list[Material]:
    stmt = select(Material).where(Material.ativo.is_(True)).order_by(Material.nome)
    return list((await db.execute(stmt)).scalars().all())


async def agregar_producao_por_produto(db: AsyncSession, data_inicio: date, data_fim: date) -> list[Row]:
    stmt = (
        select(
            Producao.produto_id,
            Produto.nome,
            func.count(Producao.id),
            func.sum(Producao.quantidade_produzida),
            func.sum(Producao.custo_total),
            func.sum(Producao.valor_total),
            func.sum(Producao.lucro_total),
        )
        .join(Produto, Produto.id == Producao.produto_id)
        .where(Producao.data_producao.between(data_inicio, data_fim))
        .group_by(Producao.produto_id, Produto.nome)
        .order_by(Produto.nome)
    )
    return list((await db.execute(stmt)).all())


async def agregar_custo_producao_por_mes(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> list[tuple[str, Decimal]]:
    mes = func.to_char(Producao.data_producao, "YYYY-MM").label("mes")
    stmt = (
        select(mes, func.sum(Producao.custo_total))
        .where(Producao.data_producao.between(data_inicio, data_fim))
        .group_by(mes)
        .order_by(mes)
    )
    return [(row[0], row[1]) for row in (await db.execute(stmt)).all()]


async def agregar_custo_desperdicio_por_mes(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> list[tuple[str, Decimal]]:
    mes = func.to_char(Desperdicio.data, "YYYY-MM").label("mes")
    stmt = (
        select(mes, func.sum(Desperdicio.custo_perda))
        .where(Desperdicio.data.between(data_inicio, data_fim))
        .group_by(mes)
        .order_by(mes)
    )
    return [(row[0], row[1]) for row in (await db.execute(stmt)).all()]


async def agregar_lucro_por_mes(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> list[tuple[str, Decimal]]:
    mes = func.to_char(Producao.data_producao, "YYYY-MM").label("mes")
    stmt = (
        select(mes, func.sum(Producao.lucro_total))
        .where(Producao.data_producao.between(data_inicio, data_fim))
        .group_by(mes)
        .order_by(mes)
    )
    return [(row[0], row[1]) for row in (await db.execute(stmt)).all()]


async def agregar_desperdicio_por_material(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> list[Row]:
    stmt = (
        select(
            Desperdicio.material_id,
            Material.nome,
            func.sum(Desperdicio.quantidade_perdida),
            func.sum(Desperdicio.custo_perda),
        )
        .join(Material, Material.id == Desperdicio.material_id)
        .where(Desperdicio.data.between(data_inicio, data_fim))
        .group_by(Desperdicio.material_id, Material.nome)
        .order_by(Material.nome)
    )
    return list((await db.execute(stmt)).all())


async def agregar_desperdicio_por_motivo(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> list[Row]:
    stmt = (
        select(Desperdicio.motivo, func.count(Desperdicio.id), func.sum(Desperdicio.custo_perda))
        .where(Desperdicio.data.between(data_inicio, data_fim))
        .group_by(Desperdicio.motivo)
        .order_by(Desperdicio.motivo)
    )
    return list((await db.execute(stmt)).all())


async def contar_materiais_ativos(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Material).where(Material.ativo.is_(True))
    return (await db.execute(stmt)).scalar_one()


async def listar_materiais_estoque_baixo(db: AsyncSession) -> list[Material]:
    stmt = (
        select(Material)
        .where(Material.ativo.is_(True), Material.quantidade_atual < Material.quantidade_minima)
        .order_by(Material.nome)
    )
    return list((await db.execute(stmt)).scalars().all())


async def contar_produtos_ativos(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Produto).where(Produto.ativo.is_(True))
    return (await db.execute(stmt)).scalar_one()


async def somar_producoes_periodo(
    db: AsyncSession, data_inicio: date, data_fim: date
) -> tuple[int, Decimal, Decimal]:
    stmt = select(
        func.count(Producao.id),
        func.coalesce(func.sum(Producao.lucro_total), 0),
        func.coalesce(func.sum(Producao.custo_total), 0),
    ).where(Producao.data_producao.between(data_inicio, data_fim))
    return (await db.execute(stmt)).one()


async def somar_desperdicio_periodo(db: AsyncSession, data_inicio: date, data_fim: date) -> Decimal:
    stmt = select(func.coalesce(func.sum(Desperdicio.custo_perda), 0)).where(
        Desperdicio.data.between(data_inicio, data_fim)
    )
    return (await db.execute(stmt)).scalar_one()


async def agregar_producoes_por_mes(db: AsyncSession, data_inicio: date, data_fim: date) -> list[Row]:
    mes = func.to_char(Producao.data_producao, "YYYY-MM").label("mes")
    stmt = (
        select(mes, func.count(Producao.id), func.sum(Producao.lucro_total))
        .where(Producao.data_producao.between(data_inicio, data_fim))
        .group_by(mes)
        .order_by(mes)
    )
    return list((await db.execute(stmt)).all())


async def top_materiais_consumidos(
    db: AsyncSession, data_inicio: date, data_fim: date, limite: int = 5
) -> list[Row]:
    stmt = (
        select(
            ProducaoItem.material_id,
            Material.nome,
            Material.unidade_base,
            func.sum(ProducaoItem.quantidade_consumida),
        )
        .join(Producao, Producao.id == ProducaoItem.producao_id)
        .join(Material, Material.id == ProducaoItem.material_id)
        .where(Producao.data_producao.between(data_inicio, data_fim))
        .group_by(ProducaoItem.material_id, Material.nome, Material.unidade_base)
        .order_by(func.sum(ProducaoItem.quantidade_consumida).desc())
        .limit(limite)
    )
    return list((await db.execute(stmt)).all())
