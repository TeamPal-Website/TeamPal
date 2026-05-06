import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.enums import Gender
from src.utils.avatar_url import client_avatar_url
_RU_NAME_RE = re.compile("^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$")

class ProfileContacts(BaseModel):
    phone: str | None = Field(None, max_length=20)
    telegram: str | None = Field(None, max_length=64)
    github: str | None = Field(None, max_length=100)

class ProfileBase(BaseModel):
    first_name: str | None = Field(None, max_length=35)
    last_name: str | None = Field(None, max_length=35)
    age: int | None = Field(None, ge=16, le=100)
    gender: Gender | None = None
    contacts: ProfileContacts | None = None

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = re.sub('\\s+', ' ', value.strip())
        if not value:
            raise ValueError('Укажите имя')
        if not _RU_NAME_RE.fullmatch(value):
            raise ValueError('Имя и фамилия — только русские буквы; допускаются дефис, апостроф и пробел между частями слова')
        return value

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = re.sub('\\s+', ' ', value.strip())
        if not value:
            raise ValueError('Укажите фамилию')
        if not _RU_NAME_RE.fullmatch(value):
            raise ValueError('Имя и фамилия — только русские буквы; допускаются дефис, апостроф и пробел между частями слова')
        return value

class ProfileRequestPatch(ProfileBase):
    pass

class ProfileAdd(ProfileBase):
    user_id: int = Field(gt=0)

class ProfileAvatarKeyUpdate(BaseModel):
    avatar: str = Field(..., max_length=255)

class Profile(ProfileBase):
    id: int
    user_id: int
    avatar: str | None = Field(None, max_length=255)
    model_config = ConfigDict(from_attributes=True)

class ProfileRead(BaseModel):
    id: int
    user_id: int
    avatar: str | None
    first_name: str | None
    last_name: str | None
    age: int | None
    gender: Gender | None
    contacts: ProfileContacts | None

    @classmethod
    def from_profile(cls, p: Profile) -> 'ProfileRead':
        return cls(id=p.id, user_id=p.user_id, avatar=client_avatar_url(p.avatar, p.user_id), first_name=p.first_name, last_name=p.last_name, age=p.age, gender=p.gender, contacts=p.contacts)

class PublicProfile(BaseModel):
    model_config = ConfigDict(from_attributes=False)
    id: int
    user_id: int
    avatar: str | None
    first_name: str | None
    last_name: str | None
    age: int | None
    gender: Gender | None

    @classmethod
    def from_profile(cls, p: Profile) -> 'PublicProfile':
        return cls(id=p.id, user_id=p.user_id, avatar=client_avatar_url(p.avatar, p.user_id), first_name=p.first_name, last_name=p.last_name, age=p.age, gender=p.gender)
