import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums import Gender

_RU_NAME_RE = re.compile(r"^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$")


class ProfileContacts(BaseModel):
    phone: str | None = Field(None, max_length=20)
    telegram: str | None = Field(None, max_length=64)
    github: str | None = Field(None, max_length=100)


class ProfileBase(BaseModel):
    avatar: str | None = Field(None, max_length=255)
    first_name: str | None = Field(None, min_length=1, max_length=35)
    last_name: str | None = Field(None, min_length=1, max_length=35)
    age: int | None = Field(None, ge=16, le=100)
    gender: Gender | None = None
    city_id: int | None = Field(None, gt=0)
    contacts: ProfileContacts | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = re.sub(r"\s+", " ", value.strip())
        if not value:
            raise ValueError("Поле не должно быть пустым")
        if not _RU_NAME_RE.fullmatch(value):
            raise ValueError(
                "Имя и фамилия — только русские буквы; допускаются дефис, апостроф и пробел между частями слова",
            )
        return value


class ProfileRequestPatch(ProfileBase):
    pass


class ProfileAdd(ProfileBase):
    user_id: int = Field(gt=0)


class Profile(ProfileRequestPatch):
    id: int

    model_config = ConfigDict(from_attributes=True)
