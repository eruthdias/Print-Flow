"""vincula desperdicio a producao

Revision ID: d73c9a5e1f20
Revises: b4f7c2a918de
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d73c9a5e1f20"
down_revision: Union[str, Sequence[str], None] = "b4f7c2a918de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("desperdicio", sa.Column("producao_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_desperdicio_producao_id",
        "desperdicio",
        "producao",
        ["producao_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_desperdicio_producao_id", "desperdicio", ["producao_id"])


def downgrade() -> None:
    op.drop_index("ix_desperdicio_producao_id", table_name="desperdicio")
    op.drop_constraint("fk_desperdicio_producao_id", "desperdicio", type_="foreignkey")
    op.drop_column("desperdicio", "producao_id")
