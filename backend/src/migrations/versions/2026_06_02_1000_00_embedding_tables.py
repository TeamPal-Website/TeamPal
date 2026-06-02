"""pgvector extension and embedding tables for recommendations."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = 'embedding_tables_01'
down_revision: Union[str, Sequence[str], None] = 'merge_heads_2026_05_06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'resume_embeddings',
        sa.Column('resume_id', sa.Integer(), sa.ForeignKey('resumes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('content_hash', sa.Text(), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_table(
        'vacancy_embeddings',
        sa.Column(
            'vacancy_id',
            sa.Integer(),
            sa.ForeignKey('project_vacancies.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('content_hash', sa.Text(), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('vacancy_embeddings')
    op.drop_table('resume_embeddings')
    op.execute('DROP EXTENSION IF EXISTS vector')
