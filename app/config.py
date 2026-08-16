import os
from dotenv import find_dotenv, load_dotenv
from dataclasses import dataclass, field

# Ищем .env файл и загружаем если найден
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)

@dataclass
class Settings:
    DATABASE_URL: str | None = field(init=False)
    LOG_LEVEL: str | None = field(init=False)

    def __post_init__(self) -> None:
        self.DATABASE_URL= os.getenv('DATABASE_URL')
        self.LOG_LEVEL= os.getenv('LOG_LEVEL', 'INFO')

        if not self.DATABASE_URL:
            raise RuntimeError('DATABASE_URL не найден!')

settings = Settings()