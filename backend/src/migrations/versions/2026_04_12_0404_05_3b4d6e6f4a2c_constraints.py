from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = '3b4d6e6f4a2c'
down_revision: Union[str, Sequence[str], None] = '1b267146fdcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_unique_constraint(None, 'cities', ['title'])
    op.create_unique_constraint(None, 'profiles', ['user_id'])

def downgrade() -> None:
    op.drop_constraint(None, 'profiles', type_='unique')
    op.drop_constraint(None, 'cities', type_='unique')
