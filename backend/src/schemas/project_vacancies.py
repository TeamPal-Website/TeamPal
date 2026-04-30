from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums import (
    CommitmentLevel,
    ContractType,
    ProjectVacancyExperience,
    SalaryType,
    Schedule,
    WorkFormat,
)

MAX_SALARY_AMOUNT_RUB = 50_000_000


def _validate_salary_amount(v: int | None) -> int | None:
    if v is None:
        return v
    if v < 0:
        raise ValueError("Сумма заработной платы не может быть отрицательной")
    if v > MAX_SALARY_AMOUNT_RUB:
        raise ValueError(
            "Превышена допустимая сумма заработной платы (не более "
            f"{MAX_SALARY_AMOUNT_RUB} ₽).",
        )
    return v


class ProjectVacancy(BaseModel):
    id: int
    project_id: int
    role_type_id: int
    experience: ProjectVacancyExperience | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    commitment_level: CommitmentLevel | None
    responsibilities: str | None
    requirements: str | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyOccupant(BaseModel):
    user_id: int
    profile_id: int
    resume_id: int
    desired_position: str | None
    first_name: str | None
    last_name: str | None
    salary_amount: int | None = None
    salary_type: SalaryType | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    commitment_level: CommitmentLevel | None = None
    contract_type: ContractType | None = None
    computed_experience_level: ProjectVacancyExperience | None = None
    about_me: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectVacancyWithOccupant(ProjectVacancy):
    role_name: str | None = None
    occupant: VacancyOccupant | None = None
    is_filled: bool = False


class ProjectVacancyRequestAdd(BaseModel):
    role_type_id: int = Field(gt=0)
    experience: ProjectVacancyExperience | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    commitment_level: CommitmentLevel | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    salary_amount: int | None = Field(default=None)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None

    @field_validator("salary_amount")
    @classmethod
    def validate_salary_request(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)


class ProjectVacancyAdd(ProjectVacancyRequestAdd):
    project_id: int


class ProjectVacancyPatch(BaseModel):
    role_type_id: int | None = Field(default=None, gt=0)
    experience: ProjectVacancyExperience | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    commitment_level: CommitmentLevel | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    salary_amount: int | None = Field(default=None)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None

    @field_validator("salary_amount")
    @classmethod
    def validate_salary_patch(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)
