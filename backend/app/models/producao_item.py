from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.material import Material


class ProducaoItem(Base):
    __tablename__ = "producao_item"
    __table_args__ = (
        CheckConstraint("quantidade_consumida > 0", name="ck_producao_item_quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producao_id: Mapped[int] = mapped_column(
        ForeignKey("producao.id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[int] = mapped_column(ForeignKey("material.id"), nullable=False)
    quantidade_consumida: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    custo_unitario_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    custo_total_item: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    producao: Mapped["Producao"] = relationship(back_populates="itens")
    material: Mapped["Material"] = relationship()
