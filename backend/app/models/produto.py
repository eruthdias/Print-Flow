from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.produto_material import ProdutoMaterial


class Produto(Base):
    __tablename__ = "produto"
    __table_args__ = (
        Index("ix_produto_nome_ativo", "nome", unique=True, postgresql_where=text("ativo = true")),
        CheckConstraint("preco_venda >= 0", name="ck_produto_preco_venda_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    composicao: Mapped[list["ProdutoMaterial"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )
