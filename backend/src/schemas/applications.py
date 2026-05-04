from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.enums import ApplicationStatus, CancelReason, CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, SalaryType, Schedule, WorkFormat
from src.schemas.resume_experiences import ResumeExperience

class ApplicationCreate(BaseModel):
    resume_id: int = Field(gt=0)
    vacancy_id: int = Field(gt=0)

class EmployerInviteResume(BaseModel):
    resume_id: int = Field(gt=0)

class ApplicationsBadgeCounts(BaseModel):
    outgoing_pending: int
    incoming_pending: int

class ApplicationAdd(BaseModel):
    resume_id: int
    vacancy_id: int
    status: ApplicationStatus = ApplicationStatus.PENDING
    employer_initiated: bool = False

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    cancel_reason: CancelReason | None = None

class Application(BaseModel):
    id: int
    resume_id: int
    vacancy_id: int
    status: ApplicationStatus
    cancel_reason: CancelReason | None
    employer_initiated: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ApplicationWithContext(BaseModel):
    id: int
    resume_id: int
    vacancy_id: int
    status: ApplicationStatus
    cancel_reason: CancelReason | None
    employer_initiated: bool = False
    created_at: datetime
    updated_at: datetime
    project_id: int
    project_title: str
    role_type_id: int
    role_name: str | None
    project_owner_user_id: int
    model_config = ConfigDict(from_attributes=True)

class ApplicationForOwner(BaseModel):
    id: int
    resume_id: int
    vacancy_id: int
    status: ApplicationStatus
    cancel_reason: CancelReason | None
    created_at: datetime
    updated_at: datetime
    applicant_profile_id: int
    applicant_user_id: int
    desired_position: str
    role_type_id: int
    role_name: str | None
    project_id: int
    project_title: str
    model_config = ConfigDict(from_attributes=True)

class ApplicationResumeForOwner(BaseModel):
    about_me: str | None
    employment_intent: EmploymentIntent
    commitment_level: CommitmentLevel | None
    work_format: WorkFormat | None
    schedule: Schedule | None
    salary_amount: int | None
    salary_type: SalaryType | None
    contract_type: ContractType | None
    computed_experience_level: ProjectVacancyExperience | None
    skill_names: list[str]
    experiences: list[ResumeExperience]

class ApplicationForOwnerDetail(ApplicationForOwner):
    contacts: dict | None
    resume_detail: ApplicationResumeForOwner | None = None

class VacancyAssignmentAdd(BaseModel):
    resume_id: int
    vacancy_id: int
    application_id: int

class VacancyAssignment(BaseModel):
    id: int
    resume_id: int
    vacancy_id: int
    application_id: int
    created_at: datetime
    released_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
