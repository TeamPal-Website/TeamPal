from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = '79e5afdaac0d'
down_revision: Union[str, Sequence[str], None] = '54a8f312b101'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_constraint('profiles_user_id_fkey', 'profiles', type_='foreignkey')
    op.create_foreign_key('profiles_user_id_fkey', 'profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')

def downgrade() -> None:
    op.drop_constraint('profiles_user_id_fkey', 'profiles', type_='foreignkey')
    op.create_foreign_key('profiles_user_id_fkey', 'profiles', 'users', ['user_id'], ['id'])
