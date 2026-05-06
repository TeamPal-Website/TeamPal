from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    @model_validator(mode='after')
    def end_date_not_in_future(self):
        if self.end_date is not None and self.end_date > date.today():
            raise ValueError('Дата окончания не может быть позже сегодняшнего дня')
        return self

class ResumeExperienceAdd(BaseModel):
    resume_id: int
    company_name: str = Field(min_length=1, max_length=255)
    role_type_id: int = Field(gt=0)
    position: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None

    @model_validator(mode='after')
    def end_date_not_in_future(self):
        if self.end_date is not None and self.end_date > date.today():
            raise ValueError('Дата окончания не может быть позже сегодняшнего дня')
        return self

class ResumeExperiencePatch(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    role_type_id: int | None = Field(default=None, gt=0)
    position: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode='after')
    def end_date_not_in_future(self):
        if self.end_date is not None and self.end_date > date.today():
            raise ValueError('Дата окончания не может быть позже сегодняшнего дня')
        return self
