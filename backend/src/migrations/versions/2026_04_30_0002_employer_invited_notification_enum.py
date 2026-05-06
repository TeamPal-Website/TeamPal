from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = 'sprint4_enum_employer_invited'
down_revision: Union[str, Sequence[str], None] = 'sprint4_b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(sa.text("\n            DO $e$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM pg_enum e\n                    JOIN pg_type t ON e.enumtypid = t.oid\n                    JOIN pg_namespace n ON n.oid = t.typnamespace\n                    WHERE n.nspname = 'public'\n                      AND t.typname = 'notification_event_enum'\n                      AND e.enumlabel = 'employer_invited'\n                ) THEN\n                    ALTER TYPE notification_event_enum ADD VALUE 'employer_invited';\n                END IF;\n            END\n            $e$;\n            "))

def downgrade() -> None:
    pass
