from pydantic import BaseModel, EmailStr, ConfigDict


class UserAdd(BaseModel):
    email: EmailStr
    hashed_password: str
    is_active: bool

class UserRequestAdd(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attribute=True)

class UserWithHashedPassword(User):
    hashed_password: str





