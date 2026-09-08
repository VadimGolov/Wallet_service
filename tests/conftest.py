import pytest
from typing import Any, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from decimal import Decimal
from functools import partial

from app.main import app
from app.database import get_db
from app.models import Wallet
from app.config import test_settings
from app.services import execute_wallet

# ---------- Настройка тестовой БД -----------
engine = create_engine(
    test_settings.DATABASE_URL,
    connect_args={'options': '-c timezone=utc'},
    pool_pre_ping=True
)
print(test_settings.DATABASE_URL)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------- Вспомогательные функции (уровень модуля) -----------
def override_get_db(session: Session) -> Generator[Session, Any, None]:
    """
    Генератор-зависимость для подмены get_db.
    """
    yield session


def clean_tables() -> None:
    """
    Очищает таблицы transactions и wallets.
    """
    with TestingSession() as session:
        session.execute(text('SET CONSTRAINTS ALL DEFERRED'))
        session.execute(text('TRUNCATE TABLE transactions, wallets RESTART IDENTITY CASCADE'))
        session.commit()


def new_wallet_in_db(db_session: Session, balance: Decimal) -> Wallet | None:
    """
    Создаёт кошелёк с указанным балансом и возвращает объект Wallet.
    """
    result = execute_wallet(db_session, balance)
    wallet_uuid = result['wallet_uuid']
    wallet = db_session.query(Wallet).filter(Wallet.uuid == wallet_uuid).first()
    return wallet


# ----------- Фикстуры -----------
@pytest.fixture(scope='session')
def client() -> Generator[TestClient, Any, None]:
    """Тестовый клиент FastAPI."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope='function')
def db_session() -> Generator[Session, Any, None]:
    """
    Создаёт сессию с реальной транзакцией.
    """
    session = TestingSession()

    app.dependency_overrides[get_db] = partial(override_get_db, session)

    yield session

    session.close()
    app.dependency_overrides.pop(get_db, None)  # аккуратно удаляем только свою зависимость

    # Очистка таблиц
    clean_tables()


@pytest.fixture(scope='function')
def create_wallet(db_session: Session) -> partial:
    """
    Фабрика для создания кошелька (реальный сервис с commit).
    Возвращает частично применённую функцию new_wallet_in_db с зафиксированной сессией.
    """
    return partial(new_wallet_in_db, db_session)


@pytest.fixture(scope='function')
def wallet(create_wallet) -> Wallet | None:
    """
    Кошелёк с балансом 100 для упрощения.
    """
    return create_wallet(Decimal('100'))