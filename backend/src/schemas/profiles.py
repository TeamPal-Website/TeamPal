from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.profiles import Gender


class ProfileContacts(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    telegram: str | None = Field(default=None, max_length=64)
    github: str | None = Field(default=None, max_length=100)


class ProfileBase(BaseModel):
    avatar: str | None = Field(default=None, max_length=255)
    first_name: str = Field(min_length=1, max_length=35)
    last_name: str = Field(min_length=1, max_length=35)
    age: int = Field(ge=16, le=100)
    gender: Gender | None = None
    city_id: int
    contacts: ProfileContacts | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не должно быть пустым")
        return value


class ProfileAdd(ProfileBase):
    user_id: int


class ProfileRequestAdd(ProfileBase):
    pass


class ProfileRequestUpdate(BaseModel):
    avatar: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, min_length=1, max_length=35)
    last_name: str | None = Field(default=None, min_length=1, max_length=35)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    city_id: int | None = Field(default=None, gt=0)
    contacts: ProfileContacts | None = None


class Profile(ProfileBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)