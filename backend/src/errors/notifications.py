from src.errors.common import ValidationError


class NotificationsMarkReadInvalid(ValidationError):
    """Вызывается, когда в запросе отметки прочитанного отсутствуют ``notification_ids`` или ``mark_all``.

    HTTP status: 422.
    """

    detail = 'Укажите notification_ids или mark_all=true'
