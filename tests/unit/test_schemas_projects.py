import pytest
from datetime import datetime
from pydantic import ValidationError
from src.schemas.projects import Project, ProjectRequestAdd, ProjectAdd, ProjectPatch
from src.schemas.project_vacancies import ProjectVacancyRequestAdd
from src.enums import EmploymentIntent, ProjectsStatus

class TestProject:

    def test_valid_project(self):
        project = Project(id=1, profile_id=1, title='My Project', company_name='Company', city_id=1, employment_intent=EmploymentIntent.COMMERCIAL, description='Description', tasks='Tasks', status=ProjectsStatus.ACTIVE, last_seen_applications_at=None, close_member_ids=None, created_at=datetime.now())
        assert project.id == 1
        assert project.title == 'My Project'

    def test_from_attributes(self):
        from types import SimpleNamespace
        orm_obj = SimpleNamespace(id=1, profile_id=1, title='Test', company_name='Company', city_id=1, employment_intent=EmploymentIntent.COMMERCIAL, description='Desc', tasks='Tasks', status=ProjectsStatus.ACTIVE, last_seen_applications_at=None, close_member_ids=None, created_at=datetime.now())
        project = Project.model_validate(orm_obj)
        assert project.id == 1

class TestProjectRequestAdd:

    def test_valid_project_request(self):
        project = ProjectRequestAdd(title='New Project', company_name='Company', employment_intent=EmploymentIntent.COMMERCIAL, vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])
        assert project.title == 'New Project'
        assert len(project.vacancies) == 1

    def test_empty_title_fails(self):
        with pytest.raises(ValidationError):
            ProjectRequestAdd(title='', vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])

    def test_whitespace_only_title_fails(self):
        with pytest.raises(ValidationError):
            ProjectRequestAdd(title='   ', vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])

    def test_strips_title_whitespace(self):
        project = ProjectRequestAdd(title='  Project  ', vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])
        assert project.title == 'Project'

    def test_title_max_length_accepted(self):
        project = ProjectRequestAdd(title='A' * 255, vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])
        assert len(project.title) == 255

    def test_title_exceeds_max_length_fails(self):
        with pytest.raises(ValidationError):
            ProjectRequestAdd(title='A' * 256, vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])

    def test_vacancies_min_length(self):
        with pytest.raises(ValidationError):
            ProjectRequestAdd(title='Project', vacancies=[])

    def test_vacancies_max_length(self):
        with pytest.raises(ValidationError):
            ProjectRequestAdd(title='Project', vacancies=[ProjectVacancyRequestAdd(role_type_id=i, description=f'Dev {i}') for i in range(11)])

    def test_duplicate_role_type_ids_allowed(self):
        project = ProjectRequestAdd(title='Project', vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev1'), ProjectVacancyRequestAdd(role_type_id=1, description='Dev2')])
        assert len(project.vacancies) == 2
        assert project.vacancies[0].role_type_id == project.vacancies[1].role_type_id

    def test_default_values(self):
        project = ProjectRequestAdd(title='Project', vacancies=[ProjectVacancyRequestAdd(role_type_id=1, description='Dev')])
        assert project.employment_intent == EmploymentIntent.COMMERCIAL
        assert project.status == ProjectsStatus.ACTIVE

class TestProjectAdd:

    def test_valid_project_add(self):
        project = ProjectAdd(profile_id=1, title='Project', employment_intent=EmploymentIntent.COMMERCIAL)
        assert project.profile_id == 1
        assert project.title == 'Project'

    def test_all_optional_fields(self):
        project = ProjectAdd(profile_id=1, title='Project', company_name='Company', city_id=1, employment_intent=EmploymentIntent.COMMERCIAL, description='Desc', tasks='Tasks', status=ProjectsStatus.ACTIVE)
        assert project.company_name == 'Company'

class TestProjectPatch:

    def test_valid_patch(self):
        patch = ProjectPatch(title='New Title')
        assert patch.title == 'New Title'

    def test_all_fields_optional(self):
        patch = ProjectPatch()
        assert patch.title is None
        assert patch.company_name is None
        assert patch.city_id is None

    def test_patch_with_multiple_fields(self):
        patch = ProjectPatch(title='New Title', company_name='New Company', employment_intent=EmploymentIntent.COMMERCIAL)
        assert patch.title == 'New Title'
        assert patch.company_name == 'New Company'
        assert patch.employment_intent == EmploymentIntent.COMMERCIAL
