"""Add employer_invited to notification_event_enum

Revision ID: sprint4_enum_employer_invited
Revises: sprint4_b1c2d3e4f5a6
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sprint4_enum_employer_invited"
down_revision: Union[str, Sequence[str], None] = "sprint4_b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $e$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE n.nspname = 'public'
                      AND t.typname = 'notification_event_enum'
                      AND e.enumlabel = 'employer_invited'
                ) THEN
                    ALTER TYPE notification_event_enum ADD VALUE 'employer_invited';
                END IF;
            END
            $e$;
            """
        )
    )


def downgrade() -> None:
    pass
