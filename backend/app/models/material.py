from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import UnidadeMedida


class Material(Base):
    __tablename__ = "material"
    __table_args__ = (
        Index("ix_material_nome_ativo", "nome", unique=True, postgresql_where=text("ativo = true")),
        CheckConstraint("fator_conversao > 0", name="ck_material_fator_conversao_positivo"),
        CheckConstraint("valor_compra >= 0", name="ck_material_valor_compra_nao_negativo"),
        CheckConstraint("quantidade_atual >= 0", name="ck_material_quantidade_atual_nao_negativa"),
        CheckConstraint("quantidade_minima >= 0", name="ck_material_quantidade_minima_nao_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    unidade_compra: Mapped[UnidadeMedida] = mapped_column(
        SAEnum(UnidadeMedida, name="unidademedida"), nullable=False
    )
    unidade_base: Mapped[UnidadeMedida] = mapped_column(
        SAEnum(UnidadeMedida, name="unidademedida"), nullable=False
    )
    fator_conversao: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("1"))
    valor_compra: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    custo_unitario_base: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    quantidade_atual: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("0"))
    quantidade_minima: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("0"))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
