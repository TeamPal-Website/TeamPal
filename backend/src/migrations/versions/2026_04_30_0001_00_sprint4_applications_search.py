"""sprint4: applications, vacancy_assignments, notifications, resume/project fields

Revision ID: sprint4_b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30 00:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sprint4_b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text("ALTER TYPE projects_status_enum ADD VALUE IF NOT EXISTS 'close'")
    )
    op.execute(
        sa.text("ALTER TYPE projects_status_enum ADD VALUE IF NOT EXISTS 'deleted'")
    )

    op.execute(sa.text("""
            DO $m$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'application_status_enum' AND n.nspname = 'public'
                ) THEN
                    CREATE TYPE public.application_status_enum AS ENUM (
                        'pending', 'accepted', 'rejected', 'cancelled'
                    );
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'cancel_reason_enum' AND n.nspname = 'public'
                ) THEN
                    CREATE TYPE public.cancel_reason_enum AS ENUM (
                        'user_withdrawn', 'user_left', 'removed_by_owner',
                        'resume_updated', 'another_accepted',
                        'project_paused', 'project_deleted', 'project_closed'
                    );
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'notification_event_enum' AND n.nspname = 'public'
                ) THEN
                    CREATE TYPE public.notification_event_enum AS ENUM (
                        'application_received', 'application_accepted',
                        'application_rejected', 'application_cancelled'
                    );
                END IF;
            END
            $m$;
            """))

    op.execute(sa.text("""
            DO $r$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'project_vacancies'
                      AND column_name = 'employment'
                ) THEN
                    ALTER TABLE public.project_vacancies
                    RENAME COLUMN employment TO commitment_level;
                END IF;
            END
            $r$;
            """))

    op.execute(sa.text("""
            DO $p$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'projects'
                      AND column_name = 'last_seen_applications_at'
                ) THEN
                    ALTER TABLE public.projects
                    ADD COLUMN last_seen_applications_at TIMESTAMPTZ;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'projects'
                      AND column_name = 'close_member_ids'
                ) THEN
                    ALTER TABLE public.projects
                    ADD COLUMN close_member_ids JSONB;
                END IF;
            END
            $p$;
            """))

    op.execute(sa.text("""
            DO $res$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                      AND column_name = 'work_format'
                ) THEN
                    ALTER TABLE public.resumes
                    ADD COLUMN work_format public.work_format_enum;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                      AND column_name = 'schedule'
                ) THEN
                    ALTER TABLE public.resumes
                    ADD COLUMN schedule public.schedule_enum;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                      AND column_name = 'salary_type'
                ) THEN
                    ALTER TABLE public.resumes
                    ADD COLUMN salary_type public.salary_type_enum;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                      AND column_name = 'contract_type'
                ) THEN
                    ALTER TABLE public.resumes
                    ADD COLUMN contract_type public.contract_type_enum;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                      AND column_name = 'computed_experience_level'
                ) THEN
                    ALTER TABLE public.resumes
                    ADD COLUMN computed_experience_level public.projects_vacancies_enum;
                END IF;
            END
            $res$;
            """))

    op.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS public.applications (
                id              SERIAL PRIMARY KEY,
                resume_id       INTEGER NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
                vacancy_id      INTEGER NOT NULL REFERENCES public.project_vacancies(id) ON DELETE CASCADE,
                status          public.application_status_enum NOT NULL DEFAULT 'pending',
                cancel_reason   public.cancel_reason_enum,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """))

    op.execute(sa.text("""
            ALTER TABLE public.applications
                DROP CONSTRAINT IF EXISTS uq_application_resume_vacancy
            """))

    op.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_active_application_resume_vacancy
                ON public.applications (resume_id, vacancy_id)
                WHERE status IN ('pending', 'accepted')
            """))

    op.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS public.vacancy_assignments (
                id              SERIAL PRIMARY KEY,
                resume_id       INTEGER NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
                vacancy_id      INTEGER NOT NULL REFERENCES public.project_vacancies(id) ON DELETE CASCADE,
                application_id  INTEGER NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                released_at     TIMESTAMPTZ
            )
            """))

    op.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_active_vacancy_assignment
                ON public.vacancy_assignments (vacancy_id)
                WHERE released_at IS NULL
            """))

    op.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_active_resume_assignment
                ON public.vacancy_assignments (resume_id)
                WHERE released_at IS NULL
            """))

    op.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS public.notifications (
                id              SERIAL PRIMARY KEY,
                user_id         INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                event           public.notification_event_enum NOT NULL,
                application_id  INTEGER REFERENCES public.applications(id) ON DELETE SET NULL,
                project_id      INTEGER REFERENCES public.projects(id) ON DELETE SET NULL,
                payload         JSONB NOT NULL DEFAULT '{}',
                is_read         BOOLEAN NOT NULL DEFAULT FALSE,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """))

    op.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
                ON public.notifications (user_id, is_read)
                WHERE is_read = FALSE
            """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS public.notifications"))
    op.execute(sa.text("DROP TABLE IF EXISTS public.vacancy_assignments"))
    op.execute(sa.text("DROP TABLE IF EXISTS public.applications"))

    op.execute(sa.text("""
            ALTER TABLE public.resumes
                DROP COLUMN IF EXISTS work_format,
                DROP COLUMN IF EXISTS schedule,
                DROP COLUMN IF EXISTS salary_type,
                DROP COLUMN IF EXISTS contract_type,
                DROP COLUMN IF EXISTS computed_experience_level
            """))

    op.execute(sa.text("""
            ALTER TABLE public.projects
                DROP COLUMN IF EXISTS last_seen_applications_at,
                DROP COLUMN IF EXISTS close_member_ids
            """))

    op.execute(sa.text("""
            DO $r$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'project_vacancies'
                      AND column_name = 'commitment_level'
                ) THEN
                    ALTER TABLE public.project_vacancies
                    RENAME COLUMN commitment_level TO employment;
                END IF;
            END
            $r$;
            """))

    op.execute(sa.text("DROP TYPE IF EXISTS public.notification_event_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS public.cancel_reason_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS public.application_status_enum"))
