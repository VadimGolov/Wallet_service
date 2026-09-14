from uuid import uuid4, UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Wallet, Transaction, TransactionStatus

from app.exceptions import ServiceError


# ---------- Вспомогательная функции (блокировка) ----------
def wallet_and_lock(db: Session, wallet_uuid: UUID) -> Wallet | None:
    """
    Получает кошелек и блокирует строку (SELECT ... FOR UPDATE).
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid).with_for_update()
    return db.execute(statement).scalars().first()

# ---------- Основные функции ----------
def create_wallet(db: Session, initial_balance: Decimal = Decimal('0')) -> Wallet:
    """
    Создаёт новый кошелек с уникальным UUID и начальным балансом.
    Никаких блокировок: это INSERT новой строки.
    """
    new_uuid = uuid4()
    new_wallet = Wallet(uuid=new_uuid, balance=initial_balance)

    db.add(new_wallet)

    return new_wallet


def get_balance(db: Session, wallet_uuid: UUID) -> Wallet:
    """
    Возвращает баланс кошелька по UUID.
    Если кошелек не найден — выбрасывает ServiceError.
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid)
    wallet = db.execute(statement).scalars().first()

    if not wallet:
        raise ServiceError(err_message=f'Кошелёк с uuid: {wallet_uuid} не найден', err_code=404)

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
    if not wallet:
        raise ServiceError(err_message=f'Кошелёк с uuid: {wallet_uuid} не найден', err_code=404)

    # Баланс не должен стать отрицательным
    if wallet.balance + amount < 0:
        raise ServiceError(err_message='Недостаточно средств для операции')

    wallet.balance += amount

    transact = Transaction(wallet=wallet, amount=amount, status=TransactionStatus.CONFIRMED)
    db.add(transact)

    return transact


def cancel_transaction(db: Session, wallet_uuid: UUID) -> Transaction:
    """
    Отменяет последнюю транзакцию для кошелька.
    1. Находим последнюю транзакцию для кошелька.
    2. Проверяем статус - если CONFIRMED продолжаем
    2. Под блокировкой кошелька восстанавливаем баланс.
    3. Изменяем статус на CANCELLED
    """

    # Блокируем кошелёк для безопасного изменения баланса
    wallet = wallet_and_lock(db, wallet_uuid)

    if not wallet:
        raise ServiceError(err_message=f'Кошелёк с uuid: {wallet_uuid} не найден', err_code=404)

    # Находим последнюю транзакцию для кошелька
    statement = (
        select(Transaction)
        .where(Transaction.wallet_uuid == wallet_uuid)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(1)
    )
    transact = db.execute(statement).scalars().first()

    if not transact:
        raise ServiceError(err_message=f'Нет транзакций для кошелька с uuid: {wallet_uuid}', err_code=404)

    if transact.status == TransactionStatus.CANCELLED:
        raise ServiceError(err_message=f'Последняя транзакция для кошелька с uuid: {wallet_uuid} уже была отменена', err_code=404)

    # Привязываем wallet к transact
    transact.wallet = wallet

    # Восстанавливаем баланса и запись нового статуса
    wallet.balance -= transact.amount
    transact.status = TransactionStatus.CANCELLED

    return transact