from src.errors.common import Conflict


class SkillAlreadyExists(Conflict):
    detail = 'Навык с таким названием уже существует'


class SkillInUse(Conflict):
    detail = 'Навык используется в резюме и не может быть удалён'
