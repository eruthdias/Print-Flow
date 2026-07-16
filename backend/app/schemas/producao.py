from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UnidadeMedida


class DesperdicioProducaoRequest(BaseModel):
    material_id: int
    quantidade_perdida: Decimal = Field(gt=0)
    motivo: str

    @field_validator("motivo")
    @classmethod
    def _motivo_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Motivo é obrigatório")
        return v


class ProducaoCreateRequest(BaseModel):
    produto_id: int
    quantidade_produzida: Decimal = Field(gt=0)
    data_producao: date | None = None
    desperdicios: list[DesperdicioProducaoRequest] = Field(default_factory=list)

    @field_validator("desperdicios")
    @classmethod
    def _materiais_nao_repetidos(
        cls, v: list[DesperdicioProducaoRequest]
    ) -> list[DesperdicioProducaoRequest]:
        ids = [item.material_id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Material duplicado nos desperdícios")
        return v


class ProducaoUpdateRequest(ProducaoCreateRequest):
    pass


class ProducaoItemOut(BaseModel):
    material_id: int
    material_nome: str
    unidade_base: UnidadeMedida
    quantidade_consumida: Decimal
    custo_unitario_snapshot: Decimal
    custo_total_item: Decimal


class DesperdicioProducaoOut(BaseModel):
    id: int
    material_id: int
    material_nome: str
    unidade_base: UnidadeMedida
    quantidade_perdida: Decimal
    motivo: str
    custo_perda: Decimal


class ProducaoOut(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    quantidade_produzida: Decimal
    data_producao: date
    custo_materiais: Decimal
    custo_desperdicios: Decimal
    custo_total: Decimal
    valor_total: Decimal
    lucro_total: Decimal
    itens: list[ProducaoItemOut]
    desperdicios: list[DesperdicioProducaoOut]


class AlertaEstoqueBaixoOut(BaseModel):
    material_id: int
    material_nome: str
    quantidade_atual: Decimal
    quantidade_minima: Decimal


class ProducaoCriadaOut(ProducaoOut):
    alertas_estoque_baixo: list[AlertaEstoqueBaixoOut] = []
