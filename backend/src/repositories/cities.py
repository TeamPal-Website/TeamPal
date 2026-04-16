from src.models.cities import CitiesOrm
from src.repositories.base import BaseRepository
from src.schemas.cities import City


class CitiesRepository(BaseRepository):
    model = CitiesOrm
    schema = City
