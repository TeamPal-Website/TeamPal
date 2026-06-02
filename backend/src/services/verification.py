"""Коды подтверждения email в Redis (TTL 10 минут)."""

import random
from src.catalog_cache import get_redis

CODE_TTL = 600
KEY_PREFIX = 'tp:email_verify:'


def _key(email: str) -> str:
    """Ключ Redis для кода подтверждения указанного email."""
    return f'{KEY_PREFIX}{email}'


async def generate_and_save_code(email: str) -> str:
    """Сгенерировать 6-значный код и сохранить в Redis."""
    code = str(random.randint(100000, 999999))
    print(f'[DEV] Код подтверждения для {email}: {code}')
    r = await get_redis()
    if r:
        await r.set(_key(email), code, ex=CODE_TTL)
    return code


async def verify_code(email: str, code: str) -> bool:
    """Проверить код. Возвращает True если совпадает, удаляет из Redis."""
    r = await get_redis()
    if not r:
        return False
    saved = await r.get(_key(email))
    if saved and saved == code:
        await r.delete(_key(email))
        return True
    return False


async def delete_code(email: str) -> None:
    """Удалить код из Redis."""
    r = await get_redis()
    if r:
        await r.delete(_key(email))
