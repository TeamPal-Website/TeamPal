from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "9017c06f3227"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $fix$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'employment_intent_enum' AND n.nspname = 'public'
                ) THEN
                    CREATE TYPE public.employment_intent_enum AS ENUM (
                        'commercial', 'noncommercial'
                    );
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'commitment_level_enum' AND n.nspname = 'public'
                ) THEN
                    CREATE TYPE public.commitment_level_enum AS ENUM (
                        'full_time', 'part_time', 'side_project'
                    );
                END IF;

                IF EXISTS (
                    SELECT 1 FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE n.nspname = 'public' AND c.relname = 'resumes'
                      AND a.attname = 'employment_intent' AND NOT a.attisdropped
                      AND t.typname = 'employment_intent'
                ) THEN
                    ALTER TABLE public.resumes
                    ALTER COLUMN employment_intent TYPE public.employment_intent_enum
                    USING employment_intent::text::public.employment_intent_enum;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE n.nspname = 'public' AND c.relname = 'resumes'
                      AND a.attname = 'commitment_level' AND NOT a.attisdropped
                      AND t.typname = 'commitment_level'
                ) THEN
                    ALTER TABLE public.resumes
                    ALTER COLUMN commitment_level TYPE public.commitment_level_enum
                    USING commitment_level::text::public.commitment_level_enum;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE n.nspname = 'public' AND c.relname = 'projects'
                      AND a.attname = 'type' AND NOT a.attisdropped
                      AND t.typname = 'employment_intent'
                ) THEN
                    ALTER TABLE public.projects
                    ALTER COLUMN "type" TYPE public.employment_intent_enum
                    USING "type"::text::public.employment_intent_enum;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE n.nspname = 'public' AND c.relname = 'project_vacancies'
                      AND a.attname = 'employment' AND NOT a.attisdropped
                      AND t.typname = 'commitment_level'
                ) THEN
                    ALTER TABLE public.project_vacancies
                    ALTER COLUMN employment TYPE public.commitment_level_enum
                    USING employment::text::public.commitment_level_enum;
                END IF;

                DROP TYPE IF EXISTS public.employment_intent;
                DROP TYPE IF EXISTS public.commitment_level;

                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'resumes'
                ) THEN
                    ALTER TABLE public.resumes ALTER COLUMN status SET DATA TYPE text USING (
                        CASE status::text
                            WHEN 'LOOKING_FOR_JOB' THEN 'looking_for_job'
                            WHEN 'NOT_LOOKING_FOR_JOB' THEN 'not_looking_for_job'
                            WHEN 'looking_for_job' THEN 'looking_for_job'
                            WHEN 'not_looking_for_job' THEN 'not_looking_for_job'
                            ELSE 'looking_for_job'
                        END
                    );

                    DROP TYPE IF EXISTS public.resume_status_enum;

                    CREATE TYPE public.resume_status_enum AS ENUM (
                        'looking_for_job',
                        'not_looking_for_job'
                    );

                    ALTER TABLE public.resumes
                    ALTER COLUMN status SET DATA TYPE public.resume_status_enum
                    USING (status::public.resume_status_enum);

                    ALTER TABLE public.resumes ALTER COLUMN status SET NOT NULL;
                END IF;
            END
            $fix$;
            """
        )
    )


def downgrade() -> None:
    pass