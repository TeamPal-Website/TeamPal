import pytest
from datetime import datetime
from pydantic import ValidationError
from src.schemas.roles_dictionary import RoleDictionary, RoleDictionaryAdd

class TestRoleDictionary:

    def test_valid_role(self):
        role = RoleDictionary(id=1, name='Backend Developer', is_active=True, created_at=datetime.now())
        assert role.id == 1
        assert role.name == 'Backend Developer'
        assert role.is_active is True

    def test_from_attributes(self):
        from types import SimpleNamespace
        orm_obj = SimpleNamespace(id=1, name='Frontend Developer', is_active=True, created_at=datetime.now())
        role = RoleDictionary.model_validate(orm_obj)
        assert role.id == 1
        assert role.name == 'Frontend Developer'

class TestRoleDictionaryAdd:

    def test_valid_role_add(self):
        role = RoleDictionaryAdd(name='DevOps Engineer')
        assert role.name == 'DevOps Engineer'

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            RoleDictionaryAdd(name='')

    def test_whitespace_only_name_fails(self):
        with pytest.raises(ValidationError):
            RoleDictionaryAdd(name='   ')

    def test_strips_whitespace(self):
        role = RoleDictionaryAdd(name='  Manager  ')
        assert role.name == 'Manager'

    def test_name_max_length_accepted(self):
        role = RoleDictionaryAdd(name='A' * 150)
        assert len(role.name) == 150

    def test_name_exceeds_max_length_fails(self):
        with pytest.raises(ValidationError):
            RoleDictionaryAdd(name='A' * 151)

    def test_name_min_length(self):
        role = RoleDictionaryAdd(name='A')
        assert role.name == 'A'
