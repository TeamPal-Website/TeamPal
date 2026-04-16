from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums import EmploymentIntent, ProjectsStatus
from src.schemas.project_vacancies import ProjectVacancyRequestAdd


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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectRequestAdd(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    city_id: int | None = Field(default=None, gt=0)
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    description: str | None = None
    tasks: str | None = None
    status: ProjectsStatus = ProjectsStatus.ACTIVE
    vacancies: list[ProjectVacancyRequestAdd] = Field(
        ...,
        min_length=1,
        max_length=10,
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Название не должно быть пустым")
        return v

    @field_validator("vacancies")
    @classmethod
    def unique_role_ids(cls, v: list[ProjectVacancyRequestAdd]) -> list[ProjectVacancyRequestAdd]:
        seen: set[int] = set()
        for row in v:
            if row.role_type_id in seen:
                raise ValueError("Дублирующийся role_type_id в списке вакансий")
            seen.add(row.role_type_id)
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

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Название не должно быть пустым")
        return v
