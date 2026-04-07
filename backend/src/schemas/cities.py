from pydantic import BaseModel, ConfigDict, Field


class CityAdd(BaseModel):
    title: str = Field(min_length=1, max_length=50)

class City(CityAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserCityAdd(BaseModel):
    user_id: int = Field(gt=0)
    city_id: int = Field(gt=0)

class UserCity(UserCityAdd):
    id: int