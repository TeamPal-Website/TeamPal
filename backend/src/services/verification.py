"""Генерация и проверка кодов подтверждения email через Redis."""

import random
from src.catalog_cache import get_redis

CODE_TTL = 600  # 10 минут
KEY_PREFIX = 'tp:email_verify:'


def _key(email: str) -> str:
    return f'{KEY_PREFIX}{email}'


async def generate_and_save_code(email: str) -> str:
    """Сгенерировать 6-значный код и сохранить в Redis."""
    code = str(random.randint(100000, 999999))
    r = await get_redis()
    if r:
        await r.set(_key(email), code, ex=CODE_TTL)
    else:
        # Fallback если Redis недоступен — просто вернём код (для dev)
        print(f'[DEV] Redis недоступен. Код: {code}')
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
