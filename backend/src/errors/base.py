class AppError(Exception):
    """Корневое исключение для API-ошибок, сопоставляемых с HTTP-ответами.

    HTTP status: 500 по умолчанию; подклассы переопределяют :attr:`status_code`.

    :ivar detail: Понятное сообщение об ошибке, возвращаемое клиенту.
    :ivar status_code: HTTP-код статуса для этой ошибки.
    """

    status_code: int = 500
    detail: str = 'Внутренняя ошибка сервера'

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)
