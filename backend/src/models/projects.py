from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, ProjectsStatus, SalaryType, Schedule, WorkFormat
from src.models.enum_helpers import enum_values

class ProjectsOrm(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey('cities.id'), nullable=True)
    employment_intent: Mapped[EmploymentIntent] = mapped_column('type', SQLEnum(EmploymentIntent, name='employment_intent_enum', values_callable=enum_values, create_type=False), nullable=False, default=EmploymentIntent.COMMERCIAL)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tasks: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectsStatus] = mapped_column(SQLEnum(ProjectsStatus, name='projects_status_enum', values_callable=enum_values), nullable=False, default=ProjectsStatus.ACTIVE)
    last_seen_applications_at: Mapped[datetime | None] = mapped_column(nullable=True)
    close_member_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    close_participants: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

class ProjectVacancyOrm(Base):
    __tablename__ = 'project_vacancies'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    role_type_id: Mapped[int] = mapped_column(ForeignKey('roles_dictionary.id', ondelete='RESTRICT'), nullable=False)
    experience: Mapped[ProjectVacancyExperience | None] = mapped_column(SQLEnum(ProjectVacancyExperience, name='projects_vacancies_enum', values_callable=enum_values), nullable=True)
    work_format: Mapped[WorkFormat | None] = mapped_column(SQLEnum(WorkFormat, name='work_format_enum', values_callable=enum_values), nullable=True)
    schedule: Mapped[Schedule | None] = mapped_column(SQLEnum(Schedule, name='schedule_enum', values_callable=enum_values), nullable=True)
    commitment_level: Mapped[CommitmentLevel | None] = mapped_column(SQLEnum(CommitmentLevel, name='commitment_level_enum', values_callable=enum_values, create_type=False), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_amount: Mapped[int | None] = mapped_column(nullable=True)
    salary_type: Mapped[SalaryType | None] = mapped_column(SQLEnum(SalaryType, name='salary_type_enum', values_callable=enum_values), nullable=True)
    contract_type: Mapped[ContractType | None] = mapped_column(SQLEnum(ContractType, name='contract_type_enum', values_callable=enum_values), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

class ProjectVacancySkillOrm(Base):
    __tablename__ = 'project_vacancy_skills'
    __table_args__ = (UniqueConstraint('vacancy_id', 'skill_id', name='uq_project_vacancy_skill'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey('project_vacancies.id', ondelete='CASCADE'), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
