from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.configs.logger import logger
from app.exceptions.catalog import CommonError, ServiceError


def service_error_handler(_request: Request, exclusion: ServiceError) -> JSONResponse:
    """
    Бизнес-ошибки сервиса.
    """
    logger.warning(f'Бизнес-ошибка [{exclusion.status_code}]: {exclusion}')
    return JSONResponse(
        status_code=exclusion.status_code,
        content={'detail': str(exclusion)},
    )


def validation_error_handler(_request: Request, exclusion: RequestValidationError) -> JSONResponse:
    """
    Ошибки валидации FastAPI приводим к единому формату {'detail': '<строка>'}.
    """
    err_list = exclusion.errors()
    log_message = f'Ошибочные данные [{status.HTTP_422_UNPROCESSABLE_CONTENT}]:'

    if not err_list:
        message = 'Отправленные данные не прошли проверку'
        logger.warning(' '.join([log_message, message]))
    else:
        first_err = err_list[0]
        location = '.'.join(str(field) for field in first_err['loc'] if field != 'body')
        message = f'Ошибочные данные в поле "{location}": {first_err["msg"]}'

        logger.warning(' '.join([log_message, first_err['msg']]))

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={'detail': message},
    )


def unhandled_exception_handler(_request: Request, exclusion: Exception) -> JSONResponse:
    """
    Всё, что не поймали раньше.
    """
    logger.exception(
        'Необработанная ошибка [{err_code}]: {method} {path}',
        err_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        method=_request.method,
        path=_request.url.path,
        exc_info=exclusion
    )
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