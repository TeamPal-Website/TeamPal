from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class ResumeExperience(BaseModel):
    id: int
    resume_id: int
    company_name: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class ResumeExperienceRequestAdd(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None


class ResumeExperienceAdd(ResumeExperienceRequestAdd):
    resume_id: int