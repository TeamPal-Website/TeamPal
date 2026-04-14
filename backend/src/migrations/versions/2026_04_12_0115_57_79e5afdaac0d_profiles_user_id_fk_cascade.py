"""profiles user_id fk cascade

Revision ID: 79e5afdaac0d
Revises: 54a8f312b101
Create Date: 2026-04-12 01:15:57.762668

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "79e5afdaac0d"
down_revision: Union[str, Sequence[str], None] = "54a8f312b101"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("profiles_user_id_fkey", "profiles", type_="foreignkey")
    op.create_foreign_key(
        "profiles_user_id_fkey",
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("profiles_user_id_fkey", "profiles", type_="foreignkey")
    op.create_foreign_key(
        "profiles_user_id_fkey",
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        )
