from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class RoleDictionary(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=150)
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoleDictionaryAdd(BaseModel):
    name: str = Field(min_length=1, max_length=150)

    @field_validator('name')
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Название не должно быть пустым')
        return v
