from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.material import Material


class ProdutoMaterial(Base):
    __tablename__ = "produto_material"
    __table_args__ = (
        UniqueConstraint("produto_id", "material_id", name="uq_produto_material"),
        CheckConstraint("quantidade_utilizada > 0", name="ck_produto_material_quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produto.id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[int] = mapped_column(ForeignKey("material.id"), nullable=False)
    quantidade_utilizada: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    produto: Mapped["Produto"] = relationship(back_populates="composicao")
    material: Mapped["Material"] = relationship()
