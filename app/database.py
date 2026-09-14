from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаём движок
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"options": "-c timezone=utc"},
    pool_pre_ping=True
)
# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Зависимость для FastAPI: отдает сессию и гарантирует закрытие.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()