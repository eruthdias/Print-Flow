from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UnidadeMedida


class ComposicaoItemRequest(BaseModel):
    material_id: int
    quantidade_utilizada: Decimal = Field(gt=0)


def _validar_composicao_nao_vazia(v: list[ComposicaoItemRequest]) -> list[ComposicaoItemRequest]:
    if not v:
        raise ValueError("Produto deve ter ao menos um material na composição")
    ids = [item.material_id for item in v]
    if len(ids) != len(set(ids)):
        raise ValueError("Material duplicado na composição")
    return v


class ProdutoCreateRequest(BaseModel):
    nome: str
    preco_venda: Decimal = Field(ge=0)
    composicao: list[ComposicaoItemRequest]

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("composicao")
    @classmethod
    def _composicao_valida(cls, v: list[ComposicaoItemRequest]) -> list[ComposicaoItemRequest]:
        return _validar_composicao_nao_vazia(v)


class ProdutoUpdateRequest(ProdutoCreateRequest):
    pass


class PreviewCustoRequest(BaseModel):
    composicao: list[ComposicaoItemRequest]

    @field_validator("composicao")
    @classmethod
    def _composicao_valida(cls, v: list[ComposicaoItemRequest]) -> list[ComposicaoItemRequest]:
        return _validar_composicao_nao_vazia(v)


class PreviewCustoResponse(BaseModel):
    custo_producao: Decimal


class ComposicaoItemOut(BaseModel):
    material_id: int
    material_nome: str
    unidade_base: UnidadeMedida
    valor_compra: Decimal
    quantidade_por_compra: Decimal
    quantidade_utilizada: Decimal
    custo_unitario_base: Decimal
    custo_item: Decimal


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco_venda: Decimal
    ativo: bool
    imagem_url: str | None
    video_url: str | None
    custo_producao: Decimal
    lucro_estimado: Decimal
    composicao: list[ComposicaoItemOut]
