from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаём движок (engine) — это «провод» к базе.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Зависимость для FastAPI: даёт сессию и гарантирует закрытие.

    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()