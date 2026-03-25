from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field


class UserAdd(BaseModel):
    email: EmailStr = Field(max_length=200)
    hashed_password: str = Field (min_length=1, max_length=200)
    is_active: bool


class UserRequestAdd(BaseModel):
    email: EmailStr = Field(description="Email пользователя", examples=["user@example.com"], min_length=6, max_length=200)
    password: str = Field(examples=["secret123"], max_length=200)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(description="Email пользователя", examples=["user@example.com"], max_length=200)
    password: str = Field(examples=["secret123"], max_length=200)
    

class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(User):
    hashed_password: str
