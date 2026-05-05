import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import settings
from src.database import Base
from src.models.users import UsersOrm
from src.models.cities import CitiesOrm
from src.models.profiles import ProfilesOrm
from src.models.resumes import ResumesOrm
from src.models.resumes import ResumeExperienceOrm
from src.models.resumes import ResumeSkillOrm
from src.models.skills import SkillsOrm
from src.models.skills import SkillAliasOrm
from src.models.projects import ProjectsOrm
from src.models.projects import ProjectVacancyOrm
from src.models.roles_dictionary import RolesDictionaryOrm
from src.models.applications import ApplicationsOrm
from src.models.applications import VacancyAssignmentsOrm
from src.models.applications import NotificationsOrm
config = context.config
config.set_main_option('sqlalchemy.url', f'{settings.DB_URL}?async_fallback=True')
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

# Ревизии, которые когда‑то были в другой ветке и исчезли из репозитория — подменяем на родителя из текущей цепочки.
_ORPHAN_ALEMBIC_REVISION_FALLBACK = {
    'users_email_verify_01': 'projects_closed_01',
}


def _repair_orphan_alembic_revision(connection) -> None:
    script = ScriptDirectory.from_config(config)
    valid_ids = {rev.revision for rev in script.walk_revisions()}
    row = connection.execute(text('SELECT version_num FROM alembic_version')).fetchone()
    if row is None:
        return
    current = row[0]
    if current in valid_ids:
        return
    replacement = _ORPHAN_ALEMBIC_REVISION_FALLBACK.get(current)
    if replacement and replacement in valid_ids:
        connection.execute(text('UPDATE alembic_version SET version_num = :v'), {'v': replacement})
        connection.commit()


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool)
    with connectable.connect() as connection:
        _repair_orphan_alembic_revision(connection)
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
