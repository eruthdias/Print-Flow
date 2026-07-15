from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import UnidadeMedida


class MaterialEstoqueBaixoOut(BaseModel):
    material_id: int
    material_nome: str
    quantidade_atual: Decimal
    quantidade_minima: Decimal
    unidade_base: UnidadeMedida


class ProducaoPorMesOut(BaseModel):
    mes: str
    quantidade: int
    lucro: Decimal


class MaterialConsumidoOut(BaseModel):
    material: str
    quantidade: Decimal
    unidade: UnidadeMedida


class DashboardResponse(BaseModel):
    data_inicio: date
    data_fim: date
    total_materiais: int
    materiais_estoque_baixo_total: int
    materiais_estoque_baixo: list[MaterialEstoqueBaixoOut]
    total_produtos: int
    producoes_realizadas: int
    lucro_estimado: Decimal
    desperdicio_total: Decimal
    custo_total_producao: Decimal
    producoes_por_mes: list[ProducaoPorMesOut]
    top_materiais_consumidos: list[MaterialConsumidoOut]
