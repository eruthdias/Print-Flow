import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import relatorio_repository as repo
from app.schemas.relatorio import (
    ItemDesperdicioMaterial,
    ItemDesperdicioMotivo,
    ItemLucroMes,
    ItemLucroProduto,
    ItemRelatorioCustoMes,
    ItemRelatorioEstoque,
    ItemRelatorioProducao,
    RelatorioCustosResponse,
    RelatorioDesperdiciosResponse,
    RelatorioEstoqueResponse,
    RelatorioLucroResponse,
    RelatorioProducaoResponse,
)

_DUAS_CASAS = Decimal("0.01")


def resolver_periodo(data_inicio: date | None, data_fim: date | None) -> tuple[date, date]:
    hoje = date.today()
    inicio = data_inicio if data_inicio is not None else hoje.replace(day=1)
    if data_fim is not None:
        fim = data_fim
    else:
        ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
        fim = hoje.replace(day=ultimo_dia)
    return inicio, fim


async def relatorio_estoque(db: AsyncSession) -> RelatorioEstoqueResponse:
    materiais = await repo.obter_estoque_atual(db)
    itens = []
    total = Decimal("0")
    for material in materiais:
        valor = (material.quantidade_atual * material.custo_unitario_base).quantize(
            _DUAS_CASAS, rounding=ROUND_HALF_UP
        )
        total += valor
        itens.append(
            ItemRelatorioEstoque(
                material_id=material.id,
                material_nome=material.nome,
                unidade_base=material.unidade_base,
                quantidade_atual=material.quantidade_atual,
                quantidade_minima=material.quantidade_minima,
                custo_unitario_base=material.custo_unitario_base,
                valor_imobilizado=valor,
                estoque_baixo=material.quantidade_atual < material.quantidade_minima,
            )
        )
    return RelatorioEstoqueResponse(itens=itens, valor_total_imobilizado=total)


async def relatorio_producao(
    db: AsyncSession, data_inicio: date | None, data_fim: date | None
) -> RelatorioProducaoResponse:
    inicio, fim = resolver_periodo(data_inicio, data_fim)
    linhas = await repo.agregar_producao_por_produto(db, inicio, fim)
    itens = [
        ItemRelatorioProducao(
            produto_id=row[0],
            produto_nome=row[1],
            quantidade_producoes=row[2],
            quantidade_produzida=row[3],
            custo_total=row[4],
            valor_total=row[5],
            lucro_total=row[6],
        )
        for row in linhas
    ]
    return RelatorioProducaoResponse(
        data_inicio=inicio,
        data_fim=fim,
        itens=itens,
        total_quantidade_producoes=sum(item.quantidade_producoes for item in itens),
        total_quantidade_produzida=sum((item.quantidade_produzida for item in itens), start=Decimal("0")),
        total_custo=sum((item.custo_total for item in itens), start=Decimal("0")),
        total_valor=sum((item.valor_total for item in itens), start=Decimal("0")),
        total_lucro=sum((item.lucro_total for item in itens), start=Decimal("0")),
    )


async def relatorio_custos(
    db: AsyncSession, data_inicio: date | None, data_fim: date | None
) -> RelatorioCustosResponse:
    inicio, fim = resolver_periodo(data_inicio, data_fim)
    producao_por_mes = dict(await repo.agregar_custo_producao_por_mes(db, inicio, fim))
    desperdicio_por_mes = dict(await repo.agregar_custo_desperdicio_por_mes(db, inicio, fim))
    meses = sorted(set(producao_por_mes) | set(desperdicio_por_mes))

    itens = []
    total_producao = Decimal("0")
    total_desperdicio = Decimal("0")
    for mes in meses:
        custo_producao = producao_por_mes.get(mes) or Decimal("0")
        custo_desperdicio = desperdicio_por_mes.get(mes) or Decimal("0")
        total_producao += custo_producao
        total_desperdicio += custo_desperdicio
        itens.append(
            ItemRelatorioCustoMes(
                mes=mes,
                custo_producao=custo_producao,
                custo_desperdicio=custo_desperdicio,
                custo_total=custo_producao + custo_desperdicio,
            )
        )

    return RelatorioCustosResponse(
        data_inicio=inicio,
        data_fim=fim,
        itens=itens,
        total_custo_producao=total_producao,
        total_custo_desperdicio=total_desperdicio,
        total_geral=total_producao + total_desperdicio,
    )


async def relatorio_lucro(
    db: AsyncSession, data_inicio: date | None, data_fim: date | None
) -> RelatorioLucroResponse:
    inicio, fim = resolver_periodo(data_inicio, data_fim)
    por_mes_linhas = await repo.agregar_lucro_por_mes(db, inicio, fim)
    por_produto_linhas = await repo.agregar_producao_por_produto(db, inicio, fim)

    por_mes = [
        ItemLucroMes(mes=mes, lucro_total=lucro or Decimal("0")) for mes, lucro in por_mes_linhas
    ]
    por_produto = [
        ItemLucroProduto(produto_id=row[0], produto_nome=row[1], lucro_total=row[6])
        for row in por_produto_linhas
    ]
    total = sum((item.lucro_total for item in por_mes), start=Decimal("0"))
    return RelatorioLucroResponse(
        data_inicio=inicio, data_fim=fim, por_mes=por_mes, por_produto=por_produto, total_lucro=total
    )


async def relatorio_desperdicios(
    db: AsyncSession, data_inicio: date | None, data_fim: date | None
) -> RelatorioDesperdiciosResponse:
    inicio, fim = resolver_periodo(data_inicio, data_fim)
    por_material_linhas = await repo.agregar_desperdicio_por_material(db, inicio, fim)
    por_motivo_linhas = await repo.agregar_desperdicio_por_motivo(db, inicio, fim)

    por_material = [
        ItemDesperdicioMaterial(
            material_id=row[0], material_nome=row[1], quantidade_total=row[2], custo_total=row[3]
        )
        for row in por_material_linhas
    ]
    por_motivo = [
        ItemDesperdicioMotivo(motivo=row[0], quantidade_ocorrencias=row[1], custo_total=row[2])
        for row in por_motivo_linhas
    ]
    total = sum((item.custo_total for item in por_material), start=Decimal("0"))
    return RelatorioDesperdiciosResponse(
        data_inicio=inicio, data_fim=fim, por_material=por_material, por_motivo=por_motivo, total_custo=total
    )
