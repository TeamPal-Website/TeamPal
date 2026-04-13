from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from src.database import Base
from src.enums import ResumeStatus


class ResumesOrm(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    about_me: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ResumeStatus] = mapped_column(
        SQLEnum(ResumeStatus, name="resume_status_enum"),
        default=ResumeStatus.LOOKING_FOR_JOB
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class ResumeExperienceOrm(Base):
    __tablename__ = "resume_experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    company_name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)