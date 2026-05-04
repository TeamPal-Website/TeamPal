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
    return bool(settings.S3_ENDPOINT_URL and settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY and settings.S3_BUCKET)

@asynccontextmanager
async def _s3_client() -> AsyncIterator[Any]:
    if not is_object_storage_configured():
        raise RuntimeError('S3 storage is not configured')
    session = get_session()
    async with session.create_client('s3', endpoint_url=settings.S3_ENDPOINT_URL, region_name=settings.S3_REGION, aws_access_key_id=settings.S3_ACCESS_KEY_ID, aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY, config=BotoConfig(signature_version='s3v4', s3={'addressing_style': settings.S3_ADDRESSING_STYLE})) as client:
        yield client

def prepare_avatar_bytes(raw: bytes, content_type: str | None) -> tuple[bytes, str, str]:
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
    body, ct, ext = await asyncio.to_thread(prepare_avatar_bytes, raw, content_type)
    key = avatar_object_key(user_id, ext)
    async with _s3_client() as client:
        await client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=body, ContentType=ct)
    return key

async def delete_avatar_key(key: str | None) -> None:
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
