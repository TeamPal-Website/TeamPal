import pytest
from pydantic import ValidationError

from src.schemas.skills import Skill, SkillAdd


class TestSkill:

    def test_valid_skill(self):
        skill = Skill(id=1, name="Python")
        assert skill.id == 1
        assert skill.name == "Python"

    def test_from_attributes(self):
        from types import SimpleNamespace
        orm_obj = SimpleNamespace(id=1, name="JavaScript")
        skill = Skill.model_validate(orm_obj)
        assert skill.id == 1
        assert skill.name == "JavaScript"


class TestSkillAdd:

    def test_valid_skill_add(self):
        skill = SkillAdd(name="Go")
        assert skill.name == "Go"

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            SkillAdd(name="")

    def test_whitespace_only_name_fails(self):
        with pytest.raises(ValidationError):
            SkillAdd(name="   ")

    def test_strips_whitespace(self):
        skill = SkillAdd(name="  Python  ")
        assert skill.name == "Python"

    def test_name_max_length_accepted(self):
        skill = SkillAdd(name="A" * 255)
        assert len(skill.name) == 255

    def test_name_exceeds_max_length_fails(self):
        with pytest.raises(ValidationError):
            SkillAdd(name="A" * 256)

    def test_name_min_length(self):
        skill = SkillAdd(name="A")
        assert skill.name == "A"