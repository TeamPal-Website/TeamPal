from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = 'X173f1a605a4a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('users', sa.Column('id', sa.Integer(), nullable=False), sa.Column('email', sa.String(length=200), nullable=False), sa.Column('hashed_password', sa.String(length=200), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('email'))

def downgrade() -> None:
    op.drop_table('users')
