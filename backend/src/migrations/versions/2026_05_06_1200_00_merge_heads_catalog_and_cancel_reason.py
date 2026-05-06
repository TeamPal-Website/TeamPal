"""Merge parallel heads: resume enum branch + catalog seed branch."""

from typing import Sequence, Union

from alembic import op

revision: str = "merge_heads_2026_05_06"
down_revision: Union[str, Sequence[str], None] = (
    "cancel_reason_employer_revoke_01",
    "catalog_seed_catalog_v1",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
