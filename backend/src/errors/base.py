class AppError(Exception):
    status_code: int = 500
    detail: str = 'Внутренняя ошибка сервера'

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)
