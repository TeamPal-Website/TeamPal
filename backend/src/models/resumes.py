from datetime import date, datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.enums import CommitmentLevel, EmploymentIntent, ResumeStatus
from src.models.enum_helpers import enum_values


class ResumesOrm(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    desired_position: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_intent: Mapped[EmploymentIntent] = mapped_column(
        SQLEnum(EmploymentIntent, name="employment_intent_enum", values_callable=enum_values),
        default=EmploymentIntent.COMMERCIAL,
    )
    commitment_level: Mapped[CommitmentLevel | None] = mapped_column(
        SQLEnum(CommitmentLevel, name="commitment_level_enum", values_callable=enum_values),
        nullable=True,
    )
    salary_amount: Mapped[int | None] = mapped_column(nullable=True)
    about_me: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ResumeStatus] = mapped_column(
        SQLEnum(ResumeStatus, name="resume_status_enum", values_callable=enum_values),
        default=ResumeStatus.LOOKING_FOR_JOB,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ResumeSkillOrm(Base):
    __tablename__ = "resume_skills"
    __table_args__ = (
        UniqueConstraint(
            "resume_id",
            "skill_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"))


class ResumeExperienceOrm(Base):
    __tablename__ = "resume_experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    company_name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
