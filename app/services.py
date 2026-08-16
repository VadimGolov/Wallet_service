from decimal import Decimal

from sqlalchemy.orm import Session
from app.repository import create_wallet, get_balance, change_balance, cancel_transaction

def execute_wallet(db: Session, initial_balance: Decimal=Decimal('0')) -> dict[str, str | Decimal]:
    if initial_balance < 0:
        raise ValueError("Начальный баланс не может быть отрицательным")

    wallet = create_wallet(db, initial_balance)

    db.commit()
    db.refresh(wallet)

    return {
        'status': 'New wallet created',
        'wallet_uuid': wallet.uuid,
        'balance': wallet.balance,
    }


def execute_balance(db: Session, wallet_uuid: str) -> dict[str, str | Decimal]:

    wallet = get_balance(db, wallet_uuid)

    return {
        'status': 'Wallet balance',
        'wallet_uuid': wallet.uuid,
        'current_balance': wallet.balance
    }


def execute_payment(db: Session, wallet_uuid: str, amount: Decimal) -> dict[str, int | str | Decimal]:
    """
    Сервис для списания средств.
    Бизнес-логика: amount должен быть строго отрицательным.
    """
    if amount >= 0:
        raise ValueError('Для списания amount должен быть строго отрицательным')

    wallet, trans = change_balance(db, wallet_uuid, amount)

    # Коммит делаем здесь: операция прошла все бизнес-проверки
    db.commit()
    db.refresh(trans)

    return {
        'status': 'Withdraw completed',
        'transaction_id': trans.id,
        'wallet_uuid': trans.wallet_uuid,
        'amount': trans.amount,
        'balance_after': wallet.balance
    }


def execute_deposit(db: Session, wallet_uuid: str, amount: Decimal) -> dict[str, int | str | Decimal]:
    """
    Сервис для зачисления средств.
    Бизнес-логика: amount должен быть строго положительным.
    """
    if amount <= 0:
        raise ValueError('Для зачисления amount должен быть строго положительным')

    wallet, trans = change_balance(db, wallet_uuid, amount)

    db.commit()
    db.refresh(trans)

    return {
        'status': 'Deposit completed',
        'transaction_id': trans.id,
        'wallet_uuid': trans.wallet_uuid,
        'amount': trans.amount,
        'balance_after': wallet.balance
    }


# def execute_cancel(db: Session, transaction_id: int, current_user_uuid: str | None = None) -> dict:
def execute_cancel(db: Session, transaction_id: int) -> dict[str, str | int | Decimal]:
    """
    Сервис для отмены транзакции.

    Сейчас — базовая реализация с коммитом.
    """
    # Пример простой проверки прав (если у Wallet есть owner_uuid):
    # wallet, transact = cancel_transaction(db, transaction_id)
    # if wallet.owner_uuid != current_user_uuid:
    #     raise PermissionError("Вы не можете отменять чужие транзакции")

    wallet, transact = cancel_transaction(db, transaction_id)

    db.commit()
    db.refresh(wallet)

    return {
        'status': 'Cancel completed',
        'transaction_id': transact.id,
        'wallet_uuid': wallet.uuid,
        'balance_after': wallet.balance,
        'reversed_amount': transact.amount
    }