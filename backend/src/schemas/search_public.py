from datetime import datetime
from pydantic import BaseModel

from src.enums import CommitmentLevel, EmploymentIntent, ProjectsStatus, ResumeStatus


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
    salary_amount: int | None
    about_me: str | None
    status: ResumeStatus
    created_at: datetime
