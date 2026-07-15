from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UnidadeMedida


class DesperdicioCreateRequest(BaseModel):
    material_id: int
    quantidade_perdida: Decimal = Field(gt=0)
    motivo: str
    data: date | None = None

    @field_validator("motivo")
    @classmethod
    def _motivo_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Motivo é obrigatório")
        return v


class DesperdicioOut(BaseModel):
    id: int
    material_id: int
    material_nome: str
    unidade_base: UnidadeMedida
    quantidade_perdida: Decimal
    motivo: str
    data: date
    custo_perda: Decimal
