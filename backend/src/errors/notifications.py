from src.errors.common import ValidationError


class NotificationsMarkReadInvalid(ValidationError):
    detail = 'Укажите notification_ids или mark_all=true'
