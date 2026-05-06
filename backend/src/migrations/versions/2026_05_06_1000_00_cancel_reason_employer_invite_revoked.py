from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'cancel_reason_employer_revoke_01'
down_revision: Union[str, Sequence[str], None] = 'resume_exp_role_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("\n        DO $m$\n        BEGIN\n            IF NOT EXISTS (\n                SELECT 1 FROM pg_enum e\n                JOIN pg_type t ON e.enumtypid = t.oid\n                JOIN pg_namespace n ON t.typnamespace = n.oid\n                WHERE n.nspname = 'public'\n                  AND t.typname = 'cancel_reason_enum'\n                  AND e.enumlabel = 'employer_invite_revoked'\n            ) THEN\n                ALTER TYPE public.cancel_reason_enum ADD VALUE 'employer_invite_revoked';\n            END IF;\n        END\n        $m$;\n        "))


def downgrade() -> None:
    pass
