import re

_RU_NAME_RE = re.compile(r"^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$")
_PHONE_RE = re.compile(r"^(\+7|8)\d{10}$")
_TG_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")
_GH_RE = re.compile(r"^https?://.+")


def profile_incomplete_message(profile):
    if profile is None:
        return "Сначала заполните личную информацию в кабинете"

    fn = profile.first_name
    ln = profile.last_name
    if fn is None or not str(fn).strip():
        return "Укажите имя в разделе «Личная информация»"
    if ln is None or not str(ln).strip():
        return "Укажите фамилию в разделе «Личная информация»"
    fn_s = re.sub(r"\s+", " ", str(fn).strip())
    ln_s = re.sub(r"\s+", " ", str(ln).strip())
    if not _RU_NAME_RE.fullmatch(fn_s) or not _RU_NAME_RE.fullmatch(ln_s):
        return "Имя и фамилия: только русские буквы, как в личном кабинете"

    if profile.age is None or profile.age < 16 or profile.age > 100:
        return "Укажите возраст (от 16 до 100 лет) в личном кабинете"

    if profile.gender is None:
        return "Выберите пол в личном кабинете"

    raw_contacts = profile.contacts
    if raw_contacts is None:
        return "Заполните контакты в личном кабинете (телефон, Telegram, GitHub)"

    if hasattr(raw_contacts, "model_dump"):
        c = raw_contacts.model_dump()
    elif isinstance(raw_contacts, dict):
        c = raw_contacts
    else:
        return "Заполните контакты в личном кабинете"

    phone = (c.get("phone") or "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone or not _PHONE_RE.match(phone):
        return "Укажите корректный российский телефон в личном кабинете"

    tg = (c.get("telegram") or "").strip()
    if not tg or not _TG_RE.match(tg):
        return "Укажите Telegram в формате @username в личном кабинете"

    gh = (c.get("github") or "").strip()
    if not gh or not _GH_RE.match(gh):
        return "Укажите ссылку на GitHub (https://…) в личном кабинете"

    return None
