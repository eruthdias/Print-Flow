from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.produto import Produto


class Producao(Base):
    __tablename__ = "producao"
    __table_args__ = (
        CheckConstraint("quantidade_produzida > 0", name="ck_producao_quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), nullable=False)
    quantidade_produzida: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    data_producao: Mapped[date_] = mapped_column(Date, nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lucro_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    produto: Mapped["Produto"] = relationship()
    itens: Mapped[list["ProducaoItem"]] = relationship(
        back_populates="producao", cascade="all, delete-orphan"
    )
    desperdicios: Mapped[list["Desperdicio"]] = relationship(
        back_populates="producao", cascade="all, delete-orphan"
    )
