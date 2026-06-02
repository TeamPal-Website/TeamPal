"""HNSW indexes on embedding columns for fast cosine distance search.

Revision ID: hnsw_indexes_01
Revises: merge_heads_2026_06_02
Create Date: 2026-06-02
"""
from alembic import op

revision = 'hnsw_indexes_01'
down_revision = 'merge_heads_2026_06_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        'CREATE INDEX IF NOT EXISTS resume_embeddings_embedding_hnsw '
        'ON resume_embeddings USING hnsw (embedding vector_cosine_ops)'
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS vacancy_embeddings_embedding_hnsw '
        'ON vacancy_embeddings USING hnsw (embedding vector_cosine_ops)'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS resume_embeddings_embedding_hnsw')
    op.execute('DROP INDEX IF EXISTS vacancy_embeddings_embedding_hnsw')
