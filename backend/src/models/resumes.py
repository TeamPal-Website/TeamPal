from datetime import date, datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.enums import (
    CommitmentLevel,
    ContractType,
    EmploymentIntent,
    ProjectVacancyExperience,
    ResumeStatus,
    SalaryType,
    Schedule,
    WorkFormat,
)
from src.models.enum_helpers import enum_values


class ResumesOrm(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    desired_position: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles_dictionary.id", ondelete="SET NULL"),
        nullable=True,
    )
    employment_intent: Mapped[EmploymentIntent] = mapped_column(
        SQLEnum(
            EmploymentIntent,
            name="employment_intent_enum",
            values_callable=enum_values,
            create_type=True,
        ),
        default=EmploymentIntent.COMMERCIAL,
    )
    commitment_level: Mapped[CommitmentLevel | None] = mapped_column(
        SQLEnum(
            CommitmentLevel,
            name="commitment_level_enum",
            values_callable=enum_values,
            create_type=True,
        ),
        nullable=True,
    )
    work_format: Mapped[WorkFormat | None] = mapped_column(
        SQLEnum(
            WorkFormat,
            name="work_format_enum",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    schedule: Mapped[Schedule | None] = mapped_column(
        SQLEnum(
            Schedule,
            name="schedule_enum",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    salary_amount: Mapped[int | None] = mapped_column(nullable=True)
    salary_type: Mapped[SalaryType | None] = mapped_column(
        SQLEnum(
            SalaryType,
            name="salary_type_enum",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    contract_type: Mapped[ContractType | None] = mapped_column(
        SQLEnum(
            ContractType,
            name="contract_type_enum",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    computed_experience_level: Mapped[ProjectVacancyExperience | None] = mapped_column(
        SQLEnum(
            ProjectVacancyExperience,
            name="projects_vacancies_enum",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    about_me: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ResumeStatus] = mapped_column(
        SQLEnum(ResumeStatus, name="resume_status_enum", values_callable=enum_values),
        default=ResumeStatus.LOOKING_FOR_JOB,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ResumeSkillOrm(Base):
    __tablename__ = "resume_skills"
    __table_args__ = (
        UniqueConstraint(
            "resume_id",
            "skill_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"))


class ResumeExperienceOrm(Base):
    __tablename__ = "resume_experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    company_name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
