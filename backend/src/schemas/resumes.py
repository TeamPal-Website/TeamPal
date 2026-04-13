from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.enums import ResumeStatus
from src.schemas.resume_experiences import ResumeExperienceRequestAdd


class Resume(BaseModel):
    id: int
    profile_id: int
    about_me: str | None
    status: ResumeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeRequestAdd(BaseModel):
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB
    experiences: list[ResumeExperienceRequestAdd] = Field(default_factory=list)


class ResumeAdd(BaseModel):
    profile_id: int
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB
