from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, ResumeStatus, SalaryType, Schedule, WorkFormat
from src.schemas.resume_experiences import ResumeExperienceRequestAdd
MAX_SALARY_AMOUNT_RUB = 50000000

class ActiveProjectBrief(BaseModel):
    project_id: int
    title: str
    employment_intent: EmploymentIntent
    application_id: int | None = None

def _validate_salary_amount(v: int | None) -> int | None:
    if v is None:
        return v
    if v < 0:
        raise ValueError('Сумма заработной платы не может быть отрицательной')
    if v > MAX_SALARY_AMOUNT_RUB:
        raise ValueError(f'Превышена допустимая сумма заработной платы (не более {MAX_SALARY_AMOUNT_RUB} ₽).')
    return v

class Resume(BaseModel):
    id: int
    profile_id: int
    desired_position: str
    role_type_id: int | None = None
    employment_intent: EmploymentIntent
    commitment_level: CommitmentLevel | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    computed_experience_level: ProjectVacancyExperience | None
    about_me: str | None
    status: ResumeStatus
    city_id: int | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResumeWithActiveProject(Resume):
    active_project: ActiveProjectBrief | None = None

class ResumeRequestAdd(BaseModel):
    role_type_id: int = Field(gt=0)
    city_id: int | None = Field(default=None, gt=0)
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    commitment_level: CommitmentLevel | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    salary_amount: int | None = Field(default=None)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None
    experiences: list[ResumeExperienceRequestAdd] = Field(default_factory=list)
    skill_ids: list[int] = Field(..., min_length=1)

    @field_validator('salary_amount')
    @classmethod
    def validate_salary_request(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)

    @field_validator('skill_ids')
    @classmethod
    def skill_ids_positive(cls, v: list[int]) -> list[int]:
        for i in v:
            if i < 1:
                raise ValueError('Идентификатор навыка должен быть положительным')
        return v

class ResumeAdd(BaseModel):
    profile_id: int
    desired_position: str = Field(min_length=1, max_length=255)
    role_type_id: int | None = None
    city_id: int | None = Field(default=None, gt=0)
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    commitment_level: CommitmentLevel | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    salary_amount: int | None = None
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None
    computed_experience_level: ProjectVacancyExperience | None = None
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB

    @field_validator('salary_amount')
    @classmethod
    def validate_salary_add(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)

class ResumePatch(BaseModel):
    desired_position: str | None = Field(None, min_length=1, max_length=255)
    role_type_id: int | None = Field(None, gt=0)
    city_id: int | None = Field(default=None, gt=0)
    employment_intent: EmploymentIntent | None = None
    commitment_level: CommitmentLevel | None = None
    work_format: WorkFormat | None = None
    schedule: Schedule | None = None
    salary_amount: int | None = Field(None)
    salary_type: SalaryType | None = None
    contract_type: ContractType | None = None
    about_me: str | None = None
    status: ResumeStatus | None = None

    @field_validator('salary_amount')
    @classmethod
    def validate_salary_patch(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)

    @field_validator('desired_position')
    @classmethod
    def strip_desired_position(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError('Желаемая должность не должна быть пустой')
        return v

class ResumeExperienceLevelPatch(BaseModel):
    computed_experience_level: ProjectVacancyExperience | None
