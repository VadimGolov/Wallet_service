import atexit
from pathlib import Path
from typing import Any, Final, Literal

from loguru import logger
from app.configs.config import settings, test_settings


ModeType = Literal['prod', 'test']


FULL_FORMAT: Final[str] = (
    '{time:YYYY-MM-DD HH:mm:ss.SSS} | '
    '{level: <8} | '
    '{name}:{function: <24}:{line} | '
    '{message}\n'
)
SERVICE_FORMAT: Final[str] = (
    '{time:YYYY-MM-DD HH:mm:ss    } | '
    '{level: <8} | '
    '{message}\n'
)


def _formatter(record: Any) -> str:
    """
    Выбирает формат в зависимости от того, помечена ли запись как сессионная.
    """
    if record['extra'].get('session'):
        return SERVICE_FORMAT
    return FULL_FORMAT

class Logging:
    """
    Класс для настройки loguru
    """

    LOG_FOLDER: Final[Path] = Path('app/logs')
    LOG_FILES: Final[dict[str, str]] = {
        'prod': 'main.log',
        'test': 'test.log',
    }

    def __init__(self, mode: ModeType) -> None:
        if mode not in self.LOG_FILES:
            raise ValueError(f'Неизвестный режим логирования: {mode}')
        self.mode = mode

    @property
    def log_level(self) -> str:
        if self.mode == 'prod':
            return settings.LOG_LEVEL
        return test_settings.LOG_LEVEL

    @property
    def log_file(self) -> Path:
        self.LOG_FOLDER.mkdir(parents=True, exist_ok=True)
        return self.LOG_FOLDER / self.LOG_FILES[self.mode]

    def setup_logger(self) -> None:
        logger.remove()

        logger.add(
            self.log_file,
            level=self.log_level,
            format=_formatter,
            rotation='10 MB',
            compression='zip',
            encoding='utf-8',
            enqueue=True,
            backtrace=True,
            diagnose=False,
        )

        logger.bind(session=True).info('--- Запуск сервиса ---')
        atexit.register(lambda: logger.bind(session=True).info('--- Остановка сервиса ---'))


def run_logger(mode: ModeType = 'prod') -> None:
    Logging(mode).setup_logger()


__all__ = ['Logging', 'run_logger', 'logger']