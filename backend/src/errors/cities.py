from src.errors.common import Conflict, ValidationError


class CityAlreadyExists(Conflict):
    detail = 'Такой город уже существует'


class CityInUse(Conflict):
    detail = 'Город указан в профилях и не может быть удалён'
