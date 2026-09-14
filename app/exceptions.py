class ServiceError(ValueError):
    """
    Класс для обработки ошибок в сервисах
    """
    def __init__(self, err_message: str, err_code: int = 400):
        super().__init__(err_message)
        self.status_code = err_code