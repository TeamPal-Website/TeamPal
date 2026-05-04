from pydantic import BaseModel, ConfigDict, Field, field_validator

class CityAdd(BaseModel):
    title: str = Field(min_length=1, max_length=50)

    @field_validator('title')
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Название не должно быть пустым')
        return v

class City(CityAdd):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserCityAdd(BaseModel):
    user_id: int = Field(gt=0)
    city_id: int = Field(gt=0)

class UserCity(UserCityAdd):
    id: int
