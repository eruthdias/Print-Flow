from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import UnidadeMedida


class OperacaoEstoque(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class MaterialCreateRequest(BaseModel):
    nome: str
    unidade_compra: UnidadeMedida
    unidade_base: UnidadeMedida
    fator_conversao: Decimal = Field(default=Decimal("1"), gt=0)
    valor_compra: Decimal = Field(ge=0)
    quantidade_atual: Decimal = Field(default=Decimal("0"), ge=0)
    quantidade_minima: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v


class MaterialUpdateRequest(BaseModel):
    nome: str
    unidade_compra: UnidadeMedida
    unidade_base: UnidadeMedida
    fator_conversao: Decimal = Field(default=Decimal("1"), gt=0)
    valor_compra: Decimal = Field(ge=0)
    quantidade_minima: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v


class AjusteEstoqueRequest(BaseModel):
    quantidade: Decimal = Field(gt=0)
    operacao: OperacaoEstoque
    observacao: str | None = None


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    unidade_compra: UnidadeMedida
    unidade_base: UnidadeMedida
    fator_conversao: Decimal
    valor_compra: Decimal
    custo_unitario_base: Decimal
    quantidade_atual: Decimal
    quantidade_minima: Decimal
    ativo: bool

    @computed_field
    @property
    def estoque_baixo(self) -> bool:
        return self.quantidade_atual < self.quantidade_minima

    @computed_field
    @property
    def quantidade_atual_unidade_compra(self) -> Decimal:
        if not self.fator_conversao:
            return Decimal("0")
        return self.quantidade_atual / self.fator_conversao


class MaterialResumoOut(BaseModel):
    materiais_cadastrados: int
    materiais_em_estoque: int
    materiais_sem_estoque: int
    produtos_cadastrados: int
    desperdicios_registrados: int
    precisando_compra: int
