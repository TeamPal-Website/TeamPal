from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums import CommitmentLevel, EmploymentIntent, ResumeStatus
from src.schemas.resume_experiences import ResumeExperienceRequestAdd

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
    salary_amount: int | None = Field(default=None)
    experiences: list[ResumeExperienceRequestAdd] = Field(default_factory=list)
    skill_ids: list[int] = Field(..., min_length=1)

    @field_validator("salary_amount")
    @classmethod
    def validate_salary_request(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)

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

    @field_validator("salary_amount")
    @classmethod
    def validate_salary_add(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)


class ResumePatch(BaseModel):
    desired_position: str | None = Field(None, min_length=1, max_length=255)
    employment_intent: EmploymentIntent | None = None
    commitment_level: CommitmentLevel | None = None
    salary_amount: int | None = Field(None)
    about_me: str | None = None
    status: ResumeStatus | None = None

    @field_validator("salary_amount")
    @classmethod
    def validate_salary_patch(cls, v: int | None) -> int | None:
        return _validate_salary_amount(v)

    @field_validator("desired_position")
    @classmethod
    def strip_desired_position(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Желаемая должность не должна быть пустой")
        return v
