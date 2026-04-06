from pydantic import BaseModel, ConfigDict


class CityAdd(BaseModel):
    title: str

class City(CityAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserCityAdd(BaseModel):
    user_id: int
    city_id: int

class UserCity(UserCityAdd):
    id: int