from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.material import Material


class Desperdicio(Base):
    __tablename__ = "desperdicio"
    __table_args__ = (
        CheckConstraint("quantidade_perdida > 0", name="ck_desperdicio_quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producao_id: Mapped[int | None] = mapped_column(
        ForeignKey("producao.id", ondelete="CASCADE"), nullable=True
    )
    material_id: Mapped[int] = mapped_column(ForeignKey("material.id"), nullable=False)
    quantidade_perdida: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[date_] = mapped_column(Date, nullable=False)
    custo_perda: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    material: Mapped["Material"] = relationship()
    producao: Mapped["Producao | None"] = relationship(back_populates="desperdicios")
