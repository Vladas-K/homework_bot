class IncorrectResponseCode(Exception):
    """Не верный код ответа."""

class RequestExceptionError(Exception):
    """Ошибка запроса."""

class ProgramCrash(Exception):
    """Сбой в работе программы."""
