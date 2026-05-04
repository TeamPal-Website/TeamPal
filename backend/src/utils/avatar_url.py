from src.config import settings


def public_avatar_url(stored: str | None) -> str | None:
    if not stored:
        return None
    s = stored.strip()
    if s.startswith("https://") or s.startswith("http://"):
        return s
    base = settings.S3_PUBLIC_BASE_URL
    if not base:
        return None
    return f"{base.rstrip('/')}/{s.lstrip('/')}"
