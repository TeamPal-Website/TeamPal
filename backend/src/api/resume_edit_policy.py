"""Shared rules for mutating resume content."""

from fastapi import HTTPException

from src.enums import ResumeStatus

ACTIVE_RESUME_DETAIL = (
    "Нельзя редактировать резюме, пока включён поиск работы. "
    "Отключите «Ищу работу» для этого резюме в личном кабинете."
)


def raise_if_resume_locked_for_editing(resume) -> None:
    if getattr(resume, "status", None) == ResumeStatus.LOOKING_FOR_JOB:
        raise HTTPException(status_code=409, detail=ACTIVE_RESUME_DETAIL)
