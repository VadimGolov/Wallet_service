from uuid import uuid4, UUID
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions.catalog import ServiceError, WalletError
from app.db.models import Transaction, TransactionStatus, Wallet


# ---------- Вспомогательная функция (блокировка) ----------
def wallet_and_lock(db: Session, wallet_uuid: UUID) -> Wallet | None:
    """
    Получает кошелёк и блокирует строку (SELECT ... FOR UPDATE).
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid).with_for_update()
    return db.execute(statement).scalars().first()


# ---------- Основные функции ----------
def create_wallet(db: Session, initial_balance: Decimal = Decimal('0')) -> Wallet:
    """
    Создаёт новый кошелёк с уникальным UUID и начальным балансом.
    Никаких блокировок: это INSERT новой строки.
    """
    new_wallet = Wallet(uuid=uuid4(), balance=initial_balance)
    db.add(new_wallet)
    return new_wallet


def delete_wallet(db: Session, wallet_uuid: UUID) -> None:
    """
    Удаляет кошелёк по UUID.
    Удаляет все транзакции по этому кошельку.
    """
    wallet = wallet_and_lock(db, wallet_uuid)

    if wallet is None:
        raise ServiceError(WalletError.WALLET_NOT_FOUND, uuid=wallet_uuid)

    if wallet.balance > 0:
        raise ServiceError(WalletError.NON_ZERO_BALANCE)

    db.execute(delete(Transaction).where(Transaction.wallet_uuid == wallet_uuid))
    db.delete(wallet)


def get_balance(db: Session, wallet_uuid: UUID) -> Wallet:
    """
    Возвращает кошелёк по UUID.
    Если кошелёк не найден — ServiceError.
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid)
    wallet = db.execute(statement).scalars().first()

    if wallet is None:
        raise ServiceError(WalletError.WALLET_NOT_FOUND, uuid=wallet_uuid)

    return wallet


def change_balance(db: Session, wallet_uuid: UUID, amount: Decimal) -> Transaction:
    """
    Применяет изменение баланса кошелька под блокировкой.

    Семантика:
      - amount < 0 → списание
      - amount > 0 → зачисление

    Здесь только целостность данных и проверка на отрицательный баланс.
    """
    wallet = wallet_and_lock(db, wallet_uuid)
    if wallet is None:
        raise ServiceError(WalletError.WALLET_NOT_FOUND, uuid=wallet_uuid)

    if wallet.balance + amount < 0:
        raise ServiceError(WalletError.INSUFFICIENT_FUNDS)

    wallet.balance += amount

    transact = Transaction(wallet=wallet, amount=amount, status=TransactionStatus.CONFIRMED)
    db.add(transact)
    return transact


def cancel_transaction(db: Session, wallet_uuid: UUID) -> Transaction:
    """
    Отменяет последнюю транзакцию для кошелька.
    1. Находим последнюю транзакцию для кошелька.
    2. Проверяем статус — если CONFIRMED, продолжаем.
    3. Под блокировкой кошелька восстанавливаем баланс.
    4. Изменяем статус на CANCELLED.
    """
    wallet = wallet_and_lock(db, wallet_uuid)

    if wallet is None:
        raise ServiceError(WalletError.WALLET_NOT_FOUND, uuid=wallet_uuid)

    statement = (
        select(Transaction)
        .where(Transaction.wallet_uuid == wallet_uuid)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(1)
    )
    transact = db.execute(statement).scalars().first()

    if not transact:
        raise ServiceError(WalletError.NO_TRANSACTIONS, uuid=wallet_uuid)

    if transact.status == TransactionStatus.CANCELLED:
        raise ServiceError(WalletError.ALREADY_CANCELLED, uuid=wallet_uuid)

    transact.wallet = wallet
    wallet.balance -= transact.amount
    transact.status = TransactionStatus.CANCELLED
    return transact