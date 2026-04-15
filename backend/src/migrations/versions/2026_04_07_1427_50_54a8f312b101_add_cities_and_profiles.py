from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "54a8f312b101"
down_revision: Union[str, Sequence[str], None] = "X173f1a605a4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=35), nullable=True),
        sa.Column("last_name", sa.String(length=35), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column(
            "gender", sa.Enum("male", "female", name="gender_enum"), nullable=True
        ),
        sa.Column("city_id", sa.Integer(), nullable=True),
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
    op.drop_table("profiles")
    op.drop_table("cities")
    op.execute(sa.text("DROP TYPE IF EXISTS gender_enum"))
