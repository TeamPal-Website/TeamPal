from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ResumeExperience(BaseModel):
    id: int
    resume_id: int
    company_name: str = Field(min_length=1, max_length=255)
    role_type_id: int | None = None
    position: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class ResumeExperienceRequestAdd(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    role_type_id: int = Field(gt=0)
    description: str | None = None
    start_date: date
    end_date: date | None = None


class ResumeExperienceAdd(BaseModel):
    resume_id: int
    company_name: str = Field(min_length=1, max_length=255)
    role_type_id: int = Field(gt=0)
    position: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None


class ResumeExperiencePatch(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    role_type_id: int | None = Field(default=None, gt=0)
    position: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
