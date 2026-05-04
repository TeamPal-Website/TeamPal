from datetime import datetime
from pydantic import BaseModel

from src.enums import (
    CommitmentLevel,
    ContractType,
    EmploymentIntent,
    ProjectVacancyExperience,
    ProjectsStatus,
    ResumeStatus,
    SalaryType,
    Schedule,
    WorkFormat,
)


class VacancySearchItem(BaseModel):
    vacancy_id: int
    role_type_id: int
    experience: ProjectVacancyExperience | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    commitment_level: CommitmentLevel | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    description: str | None
    project_id: int
    project_title: str
    project_company_name: str | None
    project_city_id: int | None
    project_employment_intent: EmploymentIntent
    project_description: str | None
    created_at: datetime


class ProjectSearchItem(BaseModel):
    id: int
    user_id: int
    profile_id: int
    title: str
    company_name: str | None
    city_id: int | None
    employment_intent: EmploymentIntent
    description: str | None
    tasks: str | None
    status: ProjectsStatus
    created_at: datetime


class ResumeSearchItem(BaseModel):
    id: int
    user_id: int
    profile_id: int
    city_id: int | None
    desired_position: str
    employment_intent: EmploymentIntent
    commitment_level: CommitmentLevel | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    computed_experience_level: ProjectVacancyExperience | None
    about_me: str | None
    skills_count: int = 0
    status: ResumeStatus
    created_at: datetime
    avatar_url: str | None = None


class RecruitingVacancyOption(BaseModel):
    vacancy_id: int
    project_id: int
    project_title: str
    role_name: str | None
