"""create new tables cities and profiles

Revision ID: 86078fe6fc8d
Revises: X173f1a605a4a
Create Date: 2026-04-06 02:29:38.224175

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "86078fe6fc8d"
down_revision: Union[str, Sequence[str], None] = "X173f1a605a4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=25), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=35), nullable=False),
        sa.Column("last_name", sa.String(length=35), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column(
            "gender", sa.Enum("MALE", "FEMALE", name="gender_enum"), nullable=True
        ),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("contacts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("profiles")
    op.drop_table("cities")
