from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import UnidadeMedida


class ItemRelatorioEstoque(BaseModel):
    material_id: int
    material_nome: str
    unidade_base: UnidadeMedida
    quantidade_atual: Decimal
    quantidade_minima: Decimal
    custo_unitario_base: Decimal
    valor_imobilizado: Decimal
    estoque_baixo: bool


class RelatorioEstoqueResponse(BaseModel):
    itens: list[ItemRelatorioEstoque]
    valor_total_imobilizado: Decimal


class ItemRelatorioProducao(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade_producoes: int
    quantidade_produzida: Decimal
    custo_total: Decimal
    valor_total: Decimal
    lucro_total: Decimal


class RelatorioProducaoResponse(BaseModel):
    data_inicio: date
    data_fim: date
    itens: list[ItemRelatorioProducao]
    total_quantidade_producoes: int
    total_quantidade_produzida: Decimal
    total_custo: Decimal
    total_valor: Decimal
    total_lucro: Decimal


class ItemRelatorioCustoMes(BaseModel):
    mes: str
    custo_producao: Decimal
    custo_desperdicio: Decimal
    custo_total: Decimal


class RelatorioCustosResponse(BaseModel):
    data_inicio: date
    data_fim: date
    itens: list[ItemRelatorioCustoMes]
    total_custo_producao: Decimal
    total_custo_desperdicio: Decimal
    total_geral: Decimal


class ItemLucroMes(BaseModel):
    mes: str
    lucro_total: Decimal


class ItemLucroProduto(BaseModel):
    produto_id: int
    produto_nome: str
    lucro_total: Decimal


class RelatorioLucroResponse(BaseModel):
    data_inicio: date
    data_fim: date
    por_mes: list[ItemLucroMes]
    por_produto: list[ItemLucroProduto]
    total_lucro: Decimal


class ItemDesperdicioMaterial(BaseModel):
    material_id: int
    material_nome: str
    quantidade_total: Decimal
    custo_total: Decimal


class ItemDesperdicioMotivo(BaseModel):
    motivo: str
    quantidade_ocorrencias: int
    custo_total: Decimal


class RelatorioDesperdiciosResponse(BaseModel):
    data_inicio: date
    data_fim: date
    por_material: list[ItemDesperdicioMaterial]
    por_motivo: list[ItemDesperdicioMotivo]
    total_custo: Decimal
