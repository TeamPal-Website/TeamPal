from src.errors.common import Conflict


class RoleAlreadyExists(Conflict):
    detail = 'Роль с таким названием уже существует'


class RoleInUse(Conflict):
    detail = 'Роль используется в проекте и не может быть удалена'
