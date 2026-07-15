from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import relatorio_repository as repo
from app.schemas.dashboard import (
    DashboardResponse,
    MaterialConsumidoOut,
    MaterialEstoqueBaixoOut,
    ProducaoPorMesOut,
)
from app.services.relatorio_service import resolver_periodo


async def montar_dashboard(
    db: AsyncSession, data_inicio: date | None, data_fim: date | None
) -> DashboardResponse:
    inicio, fim = resolver_periodo(data_inicio, data_fim)

    total_materiais = await repo.contar_materiais_ativos(db)
    materiais_baixo = await repo.listar_materiais_estoque_baixo(db)
    total_produtos = await repo.contar_produtos_ativos(db)
    qtd_producoes, lucro_estimado, custo_total_producao = await repo.somar_producoes_periodo(
        db, inicio, fim
    )
    desperdicio_total = await repo.somar_desperdicio_periodo(db, inicio, fim)
    producoes_por_mes_linhas = await repo.agregar_producoes_por_mes(db, inicio, fim)
    top_materiais_linhas = await repo.top_materiais_consumidos(db, inicio, fim)

    return DashboardResponse(
        data_inicio=inicio,
        data_fim=fim,
        total_materiais=total_materiais,
        materiais_estoque_baixo_total=len(materiais_baixo),
        materiais_estoque_baixo=[
            MaterialEstoqueBaixoOut(
                material_id=material.id,
                material_nome=material.nome,
                quantidade_atual=material.quantidade_atual,
                quantidade_minima=material.quantidade_minima,
                unidade_base=material.unidade_base,
            )
            for material in materiais_baixo
        ],
        total_produtos=total_produtos,
        producoes_realizadas=qtd_producoes,
        lucro_estimado=lucro_estimado,
        desperdicio_total=desperdicio_total,
        custo_total_producao=custo_total_producao,
        producoes_por_mes=[
            ProducaoPorMesOut(mes=mes, quantidade=quantidade, lucro=lucro or Decimal("0"))
            for mes, quantidade, lucro in producoes_por_mes_linhas
        ],
        top_materiais_consumidos=[
            MaterialConsumidoOut(material=nome, quantidade=quantidade, unidade=unidade)
            for _, nome, unidade, quantidade in top_materiais_linhas
        ],
    )
