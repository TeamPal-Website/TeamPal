from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums import CommitmentLevel, EmploymentIntent, ResumeStatus
from src.schemas.resume_experiences import ResumeExperienceRequestAdd


class Resume(BaseModel):
    id: int
    profile_id: int
    desired_position: str
    employment_intent: EmploymentIntent
    commitment_level: CommitmentLevel | None
    salary_amount: int | None
    about_me: str | None
    status: ResumeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeRequestAdd(BaseModel):
    desired_position: str = Field(default="Не указано", max_length=255)
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    commitment_level: CommitmentLevel | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    experiences: list[ResumeExperienceRequestAdd] = Field(default_factory=list)
    skill_ids: list[int] = Field(..., min_length=1)

    @field_validator("skill_ids")
    @classmethod
    def skill_ids_positive(cls, v: list[int]) -> list[int]:
        for i in v:
            if i < 1:
                raise ValueError("Идентификатор навыка должен быть положительным")
        return v


class ResumeAdd(BaseModel):
    profile_id: int
    desired_position: str = Field(min_length=1, max_length=255)
    employment_intent: EmploymentIntent = EmploymentIntent.COMMERCIAL
    commitment_level: CommitmentLevel | None = None
    salary_amount: int | None = None
    about_me: str | None = None
    status: ResumeStatus = ResumeStatus.LOOKING_FOR_JOB


class ResumePatch(BaseModel):
    desired_position: str | None = Field(None, min_length=1, max_length=255)
    employment_intent: EmploymentIntent | None = None
    commitment_level: CommitmentLevel | None = None
    salary_amount: int | None = Field(None, ge=0)
    about_me: str | None = None
    status: ResumeStatus | None = None

    @field_validator("desired_position")
    @classmethod
    def strip_desired_position(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Желаемая должность не должна быть пустой")
        return v
