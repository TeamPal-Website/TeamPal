"""merge heads: is_verified + embedding_tables

Revision ID: merge_heads_2026_06_02
Revises: 2026_06_02_is_verified, embedding_tables_01
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'merge_heads_2026_06_02'
down_revision = ('2026_06_02_is_verified', 'embedding_tables_01')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
