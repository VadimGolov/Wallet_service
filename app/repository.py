import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.models import Wallet, Transaction

# -----------------------------------------------------------------------------
# Вспомогательная функции (блокировка)
# -----------------------------------------------------------------------------
def wallet_and_lock(db: Session, wallet_uuid: str) -> Wallet | None:
    """
    Получает кошелёк с блокировкой строки (SELECT ... FOR UPDATE).
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid).with_for_update()
    return db.execute(statement).scalars().first()

# -----------------------------------------------------------------------------
# Создание кошелька
# -----------------------------------------------------------------------------
def create_wallet(db: Session, initial_balance: Decimal = Decimal('0')) -> Wallet:
    """
    Создаёт новый кошелёк с уникальным UUID и начальным балансом.
    Никаких блокировок: это INSERT новой строки.
    """
    new_uuid = str(uuid.uuid4())
    new_wallet = Wallet(uuid=new_uuid, balance=initial_balance)

    db.add(new_wallet)

    return new_wallet

# -----------------------------------------------------------------------------
# Запрос баланса (зачисление/списание)
# -----------------------------------------------------------------------------
def get_balance(db: Session, wallet_uuid: str) -> Wallet:
    """
    Возвращает баланс кошелька по UUID.
    Если кошелёк не найден — выбрасывает ValueError.
    """
    statement = select(Wallet).where(Wallet.uuid == wallet_uuid)
    wallet = db.execute(statement).scalars().first()

    if not wallet:
        raise ValueError(f'Кошелёк с uuid: {wallet_uuid} не найден')

    return wallet

# -----------------------------------------------------------------------------
# Изменение баланса (зачисление/списание)
# -----------------------------------------------------------------------------
def change_balance(db: Session, wallet_uuid: str, amount: Decimal) -> tuple[Wallet, Transaction]:
    """
    Применяет изменение баланса кошелька под блокировкой.

    Семантика:
      - amount < 0 → списание
      - amount > 0 → зачисление

    Здесь только целостность данных: проверка на отрицательный баланс.
    Проверки знака amount (бизнес-правила) должны быть в services.py.
    """
    wallet = wallet_and_lock(db, wallet_uuid)
    if not wallet:
        raise ValueError(f'Кошелёк с uuid: {wallet_uuid} не найден')

    # Проверка целостности: баланс не должен стать отрицательным
    if wallet.balance + amount < 0:
        raise ValueError("Недостаточно средств для операции")

    wallet.balance += amount

    transact = Transaction(wallet_uuid=wallet_uuid, amount=amount)
    db.add(transact)

    return wallet, transact

# -----------------------------------------------------------------------------
# Отмена транзакции
# -----------------------------------------------------------------------------
def cancel_transaction(db: Session, transaction_id: int) -> tuple[Wallet, Transaction]:
    """
    Отмена ранее созданной транзакции:
      1. Находим транзакцию.
      2. Под блокировкой кошелька восстанавливаем баланс.
      3. Удаляем транзакцию.

    Возвращает: (wallet, transaction) — чтобы сервис мог вернуть данные.
    """
    statement = select(Transaction).where(Transaction.id == transaction_id)
    transact: Transaction | None  = db.execute(statement).scalars().first()

    if not transact:
        raise ValueError(f'Транзакция с id: {transaction_id} не найдена')

    # Блокируем кошелёк для безопасного изменения баланса
    wallet = wallet_and_lock(db, transact.wallet_uuid)

    if not wallet:
        raise ValueError(f'Кошелёк с uuid: {transact.wallet_uuid} не найден')

    # Возвращаем ровно ту сумму, которая была в транзакции.
    # Если было списание (amount < 0) → баланс растёт.
    # Если было зачисление (amount > 0) → баланс падает.
    wallet.balance -= transact.amount
    db.delete(transact)

    return wallet, transact

# -----------------------------------------------------------------------------
# Для целей тестирования удаление всех записей их обеих БД
# -----------------------------------------------------------------------------

def clear_data(session: Session) -> None:
    """
    Удаляет ВСЕ записи из таблиц wallets и transactions.
    """
    # Сначала транзакции, потому что в них есть ForeignKey
    session.execute(delete(Transaction))
    # Потом кошельки
    session.execute(delete(Wallet))