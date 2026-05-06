from src.config import settings

def client_avatar_url(stored: str | None, user_id: int | None=None) -> str | None:
    if not stored:
        return None
    s = stored.strip()
    if not s:
        return None
    if s.startswith('https://') or s.startswith('http://'):
        return s
    if user_id is not None:
        return f'/profiles/{user_id}/avatar/file'
    base = settings.S3_PUBLIC_BASE_URL
    if not base:
        return None
    return f"{base.rstrip('/')}/{s.lstrip('/')}"

def public_avatar_url(stored: str | None) -> str | None:
    return client_avatar_url(stored, user_id=None)
