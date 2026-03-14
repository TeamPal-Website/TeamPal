from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field


class UserAdd(BaseModel):
    email: EmailStr
    hashed_password: str
    is_active: bool


class UserRequestAdd(BaseModel):
    email: EmailStr = Field(description="Email пользователя", examples=["user@example.com"])
    password: str = Field(examples=["secret123"])

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return value


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str
