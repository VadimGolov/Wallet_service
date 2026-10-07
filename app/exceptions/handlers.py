from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.catalog import CommonError, ServiceError


def service_error_handler(request: Request, exclusion: ServiceError) -> JSONResponse:
    """
    Бизнес-ошибки сервиса.
    """
    return JSONResponse(
        status_code=exclusion.status_code,
        content={'detail': str(exclusion)},
    )


def validation_error_handler(request: Request, exclusion: RequestValidationError) -> JSONResponse:
    """
    Ошибки валидации FastAPI приводим к единому формату {'detail': '<строка>'}.
    """
    err_list = exclusion.errors()

    if not err_list:
        message = 'Отправленные данные не прошли проверку'
    else:
        first_err = err_list[0]
        location = '.'.join(str(field) for field in first_err['loc'] if field != 'body')
        message = f'Ошибочные данные в поле "{location}": {first_err["msg"]}'

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={'detail': message},
    )


def unhandled_exception_handler(request: Request, exclusion: Exception) -> JSONResponse:
    """
    Всё, что не поймали раньше.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': CommonError.INTERNAL.value[0]},
    )


def register_handlers(app: FastAPI) -> None:
    """
    Регистрирует все обработчики.
    """
    app.add_exception_handler(ServiceError, service_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)