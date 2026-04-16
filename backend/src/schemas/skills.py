from pydantic import BaseModel, ConfigDict, Field, field_validator


class Skill(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class SkillAdd(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Название не должно быть пустым")
        return v
