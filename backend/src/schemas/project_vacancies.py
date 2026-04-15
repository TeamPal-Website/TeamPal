from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.enums import (
    CommitmentLevel,
    ContractType,
    ProjectVacancyExperience,
    SalaryType,
    Schedule,
    WorkFormat,
)


class ProjectVacancy(BaseModel):
    id: int
    project_id: int
    role_type_id: int
    experience: ProjectVacancyExperience | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    employment: CommitmentLevel | None
    responsibilities: str | None
    requirements: str | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectVacancyRequestAdd(BaseModel):
    role_type_id: int = Field(gt=0)
    experience: ProjectVacancyExperience | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    employment: CommitmentLevel | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None


class ProjectVacancyAdd(ProjectVacancyRequestAdd):
    project_id: int


class ProjectVacancyPatch(BaseModel):
    role_type_id: int | None = Field(default=None, gt=0)
    experience: ProjectVacancyExperience | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    employment: CommitmentLevel | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None
