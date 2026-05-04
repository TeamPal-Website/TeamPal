from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
revision: str = 'resume_city_01'
down_revision: Union[str, Sequence[str], None] = 'vac_desc_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('resumes', sa.Column('city_id', sa.Integer(), nullable=True))
    op.create_foreign_key('resumes_city_id_fkey', 'resumes', 'cities', ['city_id'], ['id'])
    conn = op.get_bind()
    conn.execute(text('UPDATE resumes AS r SET city_id = p.city_id FROM profiles AS p WHERE p.id = r.profile_id AND r.city_id IS NULL'))
    op.drop_constraint('profiles_city_id_fkey', 'profiles', type_='foreignkey')
    op.drop_column('profiles', 'city_id')

def downgrade() -> None:
    op.add_column('profiles', sa.Column('city_id', sa.Integer(), nullable=True))
    op.create_foreign_key('profiles_city_id_fkey', 'profiles', 'cities', ['city_id'], ['id'])
    conn = op.get_bind()
    conn.execute(text('UPDATE profiles AS p SET city_id = sub.city_id FROM (SELECT DISTINCT ON (profile_id) profile_id, city_id FROM resumes WHERE city_id IS NOT NULL ORDER BY profile_id, id DESC) AS sub WHERE p.id = sub.profile_id'))
    op.drop_constraint('resumes_city_id_fkey', 'resumes', type_='foreignkey')
    op.drop_column('resumes', 'city_id')
