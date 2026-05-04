from datetime import datetime
from sqlalchemy import ForeignKey, Index, func, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.enums import ApplicationStatus, CancelReason, NotificationEvent
from src.models.enum_helpers import enum_values

class ApplicationsOrm(Base):
    __tablename__ = 'applications'
    __table_args__ = (Index('uq_active_application_resume_vacancy', 'resume_id', 'vacancy_id', unique=True, postgresql_where=text("status IN ('pending', 'accepted')"), sqlite_where=text("status IN ('pending', 'accepted')")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey('project_vacancies.id', ondelete='CASCADE'), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus, name='application_status_enum', values_callable=enum_values), nullable=False, default=ApplicationStatus.PENDING)
    cancel_reason: Mapped[CancelReason | None] = mapped_column(SQLEnum(CancelReason, name='cancel_reason_enum', values_callable=enum_values), nullable=True)
    employer_initiated: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

class VacancyAssignmentsOrm(Base):
    __tablename__ = 'vacancy_assignments'
    __table_args__ = (Index('uq_active_vacancy_assignment', 'vacancy_id', unique=True, postgresql_where=text('released_at IS NULL'), sqlite_where=text('released_at IS NULL')), Index('uq_active_resume_assignment', 'resume_id', unique=True, postgresql_where=text('released_at IS NULL'), sqlite_where=text('released_at IS NULL')))
    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey('project_vacancies.id', ondelete='CASCADE'), nullable=False)
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)

class NotificationsOrm(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event: Mapped[NotificationEvent] = mapped_column(SQLEnum(NotificationEvent, name='notification_event_enum', values_callable=enum_values), nullable=False)
    application_id: Mapped[int | None] = mapped_column(ForeignKey('applications.id', ondelete='SET NULL'), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
