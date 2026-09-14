import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv


class Settings:
    """
    Класс для загрузки настроек из файлов .env и .testenv
    """
    def __init__(self, mode: str, base_path: Path | None = None) -> None:
        self.mode = mode
        self.base_path = (base_path or Path()).resolve()

        env_files: dict[str, Path] = {
            'prod': self.base_path / '.env',
            'test': self.base_path / '.testenv',
        }

        self.env_file: Path | None = env_files.get(self.mode)
        if self.env_file is None:
            raise ValueError(f'Неизвестный режим: {mode}')

        if self.env_file.exists():
            load_dotenv(self.env_file)
        else:
            pass

        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        if not self.DATABASE_URL:
            raise RuntimeError(f'DATABASE_URL не найден!')


found_env: str = find_dotenv()
env_path: Path = Path(found_env).parent if found_env else Path()

settings = Settings('prod', env_path)
test_settings = Settings('test', env_path)