from typing import Annotated

from fastapi import Depends, Query, Request, HTTPException

from src.services.auth import AuthService

from src.database import async_session_maker
from src.utils.db_manager import DBManager


def get_token(request: Request):
    token = request.cookies.get("access_token", None)
    if not token:
        raise HTTPException(status_code=401, detail="Вы не предоставили токен доступа")
    return token


def get_current_user_id(token: str = Depends(get_token)):
    data = AuthService().decode_token(token)
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Невалидный токен")
    return user_id


UserIdDep = Annotated[int, Depends(get_current_user_id)]


def get_optional_user_id(request: Request) -> int | None:
    token = request.cookies.get("access_token", None)
    if not token:
        return None
    try:
        data = AuthService().decode_token(token)
        uid = data.get("user_id")
        return int(uid) if uid is not None else None
    except Exception:
        return None


OptionalViewerIdDep = Annotated[int | None, Depends(get_optional_user_id)]


async def get_db():
    async with DBManager(session_factory=async_session_maker) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
PageDep = Annotated[int, Query(ge=1)]
PerPageDep = Annotated[int, Query(ge=1, le=50)]


def normalize_search_q(q: str | None = Query(default=None, max_length=100)):
    if q is None:
        return None
    q = q.strip()
    return q or None


SearchQDep = Annotated[str | None, Depends(normalize_search_q)]
