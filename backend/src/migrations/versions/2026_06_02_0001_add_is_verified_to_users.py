"""add is_verified to users

Revision ID: 2026_06_02_is_verified
Revises: 2026_05_20_1400_00_seed_roles_and_skills
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = '2026_06_02_is_verified'
down_revision = 'merge_heads_2026_05_06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
