"""Проверка заполненности профиля перед чувствительными действиями."""

import re

_RU_NAME_RE = re.compile("^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$")
_PHONE_RE = re.compile(r"^(\+7|8)\d{10}$")
_TG_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")
_GH_RE = re.compile(r"^https?://.+")

PROFILE_INCOMPLETE_MSG = "Заполните полностью данные в Личном кабинете"


def profile_incomplete_message(profile) -> str | None:
    """Проверить полноту профиля и вернуть текст ошибки либо ``None``.

    Профиль считается полным, если заданы корректные имя и фамилия (кириллица),
    возраст 16–100, пол и контакты (телефон, Telegram, GitHub) в валидном формате.

    :param profile: Экземпляр ORM/схемы профиля либо ``None``.
    :returns: Сообщение об ошибке, если профиль неполон, иначе ``None``.
    :rtype: str | None
    """
    if profile is None:
        return PROFILE_INCOMPLETE_MSG
    fn = profile.first_name
    ln = profile.last_name
    if fn is None or not str(fn).strip() or ln is None or not str(ln).strip():
        return PROFILE_INCOMPLETE_MSG
    fn_s = re.sub(r"\s+", " ", str(fn).strip())
    ln_s = re.sub(r"\s+", " ", str(ln).strip())
    if not _RU_NAME_RE.fullmatch(fn_s) or not _RU_NAME_RE.fullmatch(ln_s):
        return PROFILE_INCOMPLETE_MSG
    if profile.age is None or profile.age < 16 or profile.age > 100:
        return PROFILE_INCOMPLETE_MSG
    if profile.gender is None:
        return PROFILE_INCOMPLETE_MSG
    raw_contacts = profile.contacts
    if raw_contacts is None:
        return PROFILE_INCOMPLETE_MSG
    if hasattr(raw_contacts, "model_dump"):
        c = raw_contacts.model_dump()
    elif isinstance(raw_contacts, dict):
        c = raw_contacts
    else:
        return PROFILE_INCOMPLETE_MSG
    phone = (c.get("phone") or "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone or not _PHONE_RE.match(phone):
        return PROFILE_INCOMPLETE_MSG
    tg = (c.get("telegram") or "").strip()
    if not tg or not _TG_RE.match(tg):
        return PROFILE_INCOMPLETE_MSG
    gh = (c.get("github") or "").strip()
    if not gh or not _GH_RE.match(gh):
        return PROFILE_INCOMPLETE_MSG
    return None
