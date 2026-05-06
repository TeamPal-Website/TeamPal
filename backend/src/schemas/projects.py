from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.enums import EmploymentIntent, ProjectsStatus
from src.schemas.project_vacancies import ProjectVacancyRequestAdd

class CloseParticipant(BaseModel):
    user_id: int
    resume_id: int

class Project(BaseModel):
    id: int
    profile_id: int
    title: str
    company_name: str | None
    city_id: int | None
    employment_intent: EmploymentIntent
    description: str | None
    tasks: str | None
    status: ProjectsStatus
    last_seen_applications_at: datetime | None
    close_member_ids: list[int] | None
    closed_at: datetime | None = None
    close_participants: list[CloseParticipant] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ClosedProjectParticipationItem(BaseModel):
    project: Project
    my_resume_ids: list[int]

class ProjectRequestAdd(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    city_id: int | None = Field(default=None, gt=0)
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    description: str | None = None
    tasks: str | None = None
    status: ProjectsStatus = ProjectsStatus.ACTIVE
    vacancies: list[ProjectVacancyRequestAdd] = Field(..., min_length=1, max_length=10)

    @field_validator('title')
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Название не должно быть пустым')
        return v

    @field_validator('status')
    @classmethod
    def validate_initial_status(cls, v: ProjectsStatus) -> ProjectsStatus:
        if v in (ProjectsStatus.CLOSE, ProjectsStatus.DELETED):
            raise ValueError('Проект нельзя создать сразу в этом статусе')
        return v

class ProjectAdd(BaseModel):
    profile_id: int
    title: str = Field(min_length=1, max_length=255)
    company_name: str | None = None
    city_id: int | None = None
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    description: str | None = None
    tasks: str | None = None
    status: ProjectsStatus = ProjectsStatus.ACTIVE

class ProjectPatch(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    city_id: int | None = Field(None, gt=0)
    employment_intent: EmploymentIntent | None = None
    description: str | None = None
    tasks: str | None = None
    status: ProjectsStatus | None = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: ProjectsStatus | None) -> ProjectsStatus | None:
        if v in (ProjectsStatus.CLOSE, ProjectsStatus.DELETED):
            raise ValueError('Статус нельзя установить напрямую через этот метод')
        return v

    @field_validator('title')
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError('Название не должно быть пустым')
        return v
