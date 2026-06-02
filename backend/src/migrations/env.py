import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import settings
from src.database import Base
from src.models.applications import ApplicationsOrm  # noqa: F401
from src.models.applications import NotificationsOrm  # noqa: F401
from src.models.applications import VacancyAssignmentsOrm  # noqa: F401
from src.models.cities import CitiesOrm  # noqa: F401
from src.models.profiles import ProfilesOrm  # noqa: F401
from src.models.embeddings import ResumeEmbeddingOrm  # noqa: F401
from src.models.embeddings import VacancyEmbeddingOrm  # noqa: F401
from src.models.projects import ProjectVacancyOrm  # noqa: F401
from src.models.projects import ProjectsOrm  # noqa: F401
from src.models.resumes import ResumeExperienceOrm  # noqa: F401
from src.models.resumes import ResumeSkillOrm  # noqa: F401
from src.models.resumes import ResumesOrm  # noqa: F401
from src.models.roles_dictionary import RolesDictionaryOrm  # noqa: F401
from src.models.skills import SkillAliasOrm  # noqa: F401
from src.models.skills import SkillsOrm  # noqa: F401
from src.models.users import UsersOrm  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", f"{settings.DB_URL}?async_fallback=True")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
