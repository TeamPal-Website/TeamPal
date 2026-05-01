import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.resumes import Resume, ResumeRequestAdd, ResumeAdd, ResumePatch
from src.enums import EmploymentIntent, WorkFormat, ResumeStatus, CommitmentLevel


class TestResume:

    def test_valid_resume(self):
        resume = Resume(
            id=1,
            profile_id=1,
            desired_position="Python Developer",
            employment_intent=EmploymentIntent.COMMERCIAL,
            commitment_level=CommitmentLevel.FULL_TIME,
            salary_amount=100000,
            about_me="Experienced developer",
            status=ResumeStatus.LOOKING_FOR_JOB,
            created_at=datetime.now(),
        )
        assert resume.id == 1
        assert resume.desired_position == "Python Developer"

    def test_from_attributes(self):
        from types import SimpleNamespace
        orm_obj = SimpleNamespace(
            id=1,
            profile_id=1,
            desired_position="Developer",
            employment_intent=EmploymentIntent.COMMERCIAL,
            commitment_level=CommitmentLevel.PART_TIME,
            salary_amount=50000,
            about_me="About me",
            status=ResumeStatus.LOOKING_FOR_JOB,
            created_at=datetime.now(),
        )
        resume = Resume.model_validate(orm_obj)
        assert resume.id == 1


class TestResumeRequestAdd:

    def test_valid_resume_request(self):
        resume = ResumeRequestAdd(
            desired_position="Backend Developer",
            employment_intent=EmploymentIntent.COMMERCIAL,
            skill_ids=[1, 2],
        )
        assert resume.desired_position == "Backend Developer"
        assert len(resume.skill_ids) == 2

    def test_default_values(self):
        resume = ResumeRequestAdd(skill_ids=[1])
        assert resume.desired_position == "Не указано"
        assert resume.status == ResumeStatus.LOOKING_FOR_JOB
        assert resume.employment_intent == EmploymentIntent.COMMERCIAL

    def test_empty_skill_ids_fails(self):
        with pytest.raises(ValidationError):
            ResumeRequestAdd(skill_ids=[])

    def test_skill_ids_must_be_positive(self):
        with pytest.raises(ValidationError):
            ResumeRequestAdd(skill_ids=[0])

    def test_negative_salary_fails(self):
        with pytest.raises(ValidationError):
            ResumeRequestAdd(salary_amount=-1000, skill_ids=[1])

    def test_salary_exceeds_max_fails(self):
        with pytest.raises(ValidationError):
            ResumeRequestAdd(salary_amount=60_000_000, skill_ids=[1])

    def test_valid_salary_accepted(self):
        resume = ResumeRequestAdd(salary_amount=50_000_000, skill_ids=[1])
        assert resume.salary_amount == 50_000_000

    def test_title_max_length_accepted(self):
        resume = ResumeRequestAdd(
            desired_position="A" * 255,
            skill_ids=[1],
        )
        assert len(resume.desired_position) == 255

    def test_title_exceeds_max_length_fails(self):
        with pytest.raises(ValidationError):
            ResumeRequestAdd(
                desired_position="A" * 256,
                skill_ids=[1],
            )


class TestResumeAdd:

    def test_valid_resume_add(self):
        resume = ResumeAdd(
            profile_id=1,
            desired_position="Developer",
            employment_intent=EmploymentIntent.COMMERCIAL,
        )
        assert resume.profile_id == 1
        assert resume.desired_position == "Developer"

    def test_empty_title_fails(self):
        with pytest.raises(ValidationError):
            ResumeAdd(
                profile_id=1,
                desired_position="",
            )

    def test_all_optional_fields(self):
        resume = ResumeAdd(
            profile_id=1,
            desired_position="Developer",
            employment_intent=EmploymentIntent.COMMERCIAL,
            commitment_level=CommitmentLevel.FULL_TIME,
            salary_amount=100000,
            about_me="About me",
            status=ResumeStatus.LOOKING_FOR_JOB,
        )
        assert resume.salary_amount == 100000


class TestResumePatch:

    def test_valid_patch(self):
        patch = ResumePatch(desired_position="New Position")
        assert patch.desired_position == "New Position"

    def test_all_fields_optional(self):
        patch = ResumePatch()
        assert patch.desired_position is None
        assert patch.employment_intent is None

    def test_patch_with_multiple_fields(self):
        patch = ResumePatch(
            desired_position="New Position",
            employment_intent=EmploymentIntent.COMMERCIAL,
            salary_amount=150000,
        )
        assert patch.desired_position == "New Position"
        assert patch.employment_intent == EmploymentIntent.COMMERCIAL
        assert patch.salary_amount == 150000