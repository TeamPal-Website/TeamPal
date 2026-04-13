from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from src.enums import ResumeStatus


class Resume(BaseModel):
    id: int
    profile_id: int
    about_me: str | None
    status: ResumeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
