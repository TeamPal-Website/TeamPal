"""Загрузка и удаление аватаров в S3/MinIO."""

import asyncio
import io
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Final
from aiobotocore.session import get_session
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from PIL import Image, ImageOps
from src.config import settings
MAX_AVATAR_BYTES: Final[int] = 2 * 1024 * 1024
ALLOWED_UPLOAD_CONTENT_TYPES: Final[frozenset[str]] = frozenset({'image/jpeg', 'image/png', 'image/webp'})
MIME_TO_EXT: Final[dict[str, str]] = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}
_THUMB_MAX: Final[int] = 512

def is_object_storage_configured() -> bool:
    """Проверить, заданы ли необходимые параметры S3.

    :returns: ``True``, если настроены endpoint, учётные данные и bucket.
    :rtype: bool
    """
    return bool(settings.S3_ENDPOINT_URL and settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY and settings.S3_BUCKET)

@asynccontextmanager
async def _s3_client() -> AsyncIterator[Any]:
    """Предоставить настроенный async S3-клиент на время контекста.

    :yields: Экземпляр S3-клиента aiobotocore.
    :rtype: AsyncIterator[Any]
    :raises RuntimeError: Если объектное хранилище не настроено.
    """
    if not is_object_storage_configured():
        raise RuntimeError('S3 storage is not configured')
    session = get_session()
    async with session.create_client('s3', endpoint_url=settings.S3_ENDPOINT_URL, region_name=settings.S3_REGION, aws_access_key_id=settings.S3_ACCESS_KEY_ID, aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY, config=BotoConfig(signature_version='s3v4', s3={'addressing_style': settings.S3_ADDRESSING_STYLE})) as client:
        yield client

def prepare_avatar_bytes(raw: bytes, content_type: str | None) -> tuple[bytes, str, str]:
    """Проверить, нормализовать ориентацию и изменить размер байтов изображения аватара.

    :param raw: Сырые байты загруженного изображения.
    :type raw: bytes
    :param content_type: Заявленный MIME-тип загрузки.
    :type content_type: str | None
    :returns: Кортеж из обработанного тела, нормализованного MIME-типа и расширения файла.
    :rtype: tuple[bytes, str, str]
    :raises ValueError: Если размер, MIME-тип или формат изображения недопустимы.
    """
    if len(raw) > MAX_AVATAR_BYTES:
        raise ValueError('Размер файла не больше 2 МБ')
    ct = (content_type or '').split(';')[0].strip().lower()
    if ct not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValueError('Допустимы только JPEG, PNG или WebP')
    im = Image.open(io.BytesIO(raw))
    im.load()
    if im.format not in ('JPEG', 'PNG', 'WEBP'):
        raise ValueError('Недопустимый формат изображения')
    im = ImageOps.exif_transpose(im)
    im.thumbnail((_THUMB_MAX, _THUMB_MAX), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    ext = MIME_TO_EXT[ct]
    if ext == 'jpg':
        im.convert('RGB').save(buf, format='JPEG', quality=88, optimize=True)
        return (buf.getvalue(), 'image/jpeg', 'jpg')
    if ext == 'png':
        im.save(buf, format='PNG', optimize=True)
        return (buf.getvalue(), 'image/png', 'png')
    im.save(buf, format='WEBP', quality=85, method=4)
    return (buf.getvalue(), 'image/webp', 'webp')

def avatar_object_key(user_id: int, ext: str) -> str:
    """Сформировать уникальный ключ S3-объекта для аватара пользователя.

    :param user_id: Идентификатор пользователя-владельца.
    :type user_id: int
    :param ext: Расширение файла без ведущей точки.
    :type ext: str
    :returns: Ключ объекта в настроенном префиксе аватаров.
    :rtype: str
    """
    prefix = settings.S3_AVATAR_PREFIX.strip('/')
    if prefix:
        prefix = prefix + '/'
    safe_ext = ext.lower().lstrip('.')
    if safe_ext not in {'jpg', 'jpeg', 'png', 'webp'}:
        safe_ext = 'jpg'
    if safe_ext == 'jpeg':
        safe_ext = 'jpg'
    return f'{prefix}{user_id}/{uuid.uuid4().hex}.{safe_ext}'

async def upload_avatar(user_id: int, raw: bytes, content_type: str | None) -> str:
    """Обработать и загрузить изображение аватара в объектное хранилище.

    :param user_id: Идентификатор пользователя-владельца.
    :type user_id: int
    :param raw: Сырые байты загруженного изображения.
    :type raw: bytes
    :param content_type: Заявленный MIME-тип загрузки.
    :type content_type: str | None
    :returns: Ключ S3-объекта сохранённого аватара.
    :rtype: str
    :raises ValueError: Если проверка изображения не пройдена.
    :raises RuntimeError: Если объектное хранилище не настроено.
    """
    body, ct, ext = await asyncio.to_thread(prepare_avatar_bytes, raw, content_type)
    key = avatar_object_key(user_id, ext)
    async with _s3_client() as client:
        await client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=body, ContentType=ct)
    return key

async def delete_avatar_key(key: str | None) -> None:
    """Удалить объект аватара из хранилища, игнорируя legacy URL-ключи.

    :param key: Сохранённый ключ объекта, внешний URL или ``None``.
    :type key: str | None
    """
    if not key or key.startswith('http://') or key.startswith('https://'):
        return
    if not is_object_storage_configured():
        return
    try:
        async with _s3_client() as client:
            await client.delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except ClientError:
        pass

async def get_object_bytes(key: str) -> tuple[bytes, str] | None:
    """Получить байты объекта и content type из хранилища.

    :param key: Сохранённый ключ объекта или внешний URL.
    :type key: str
    :returns: Кортеж из тела и content type, или ``None``, если объект недоступен.
    :rtype: tuple[bytes, str] | None
    :raises ClientError: Если S3 вернул ошибку, отличную от отсутствия объекта.
    """
    if not key or key.startswith('http://') or key.startswith('https://'):
        return None
    if not is_object_storage_configured():
        return None
    try:
        async with _s3_client() as client:
            resp = await client.get_object(Bucket=settings.S3_BUCKET, Key=key)
            body = await resp['Body'].read()
            ct = resp.get('ContentType') or 'application/octet-stream'
            return (body, ct)
    except ClientError as exc:
        err = exc.response.get('Error') or {}
        code = err.get('Code', '')
        if code in ('NoSuchKey', '404', 'NotFound'):
            return None
        raise
