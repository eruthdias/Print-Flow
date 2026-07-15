"""adiciona imagem e video ao produto

Revision ID: b4f7c2a918de
Revises: 6ff5a474f2c2
Create Date: 2026-07-13 11:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4f7c2a918de"
down_revision: Union[str, Sequence[str], None] = "6ff5a474f2c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("produto", sa.Column("imagem_url", sa.String(length=255), nullable=True))
    op.add_column("produto", sa.Column("video_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("produto", "video_url")
    op.drop_column("produto", "imagem_url")
