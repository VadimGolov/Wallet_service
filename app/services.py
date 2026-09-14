from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session
from app.repository import create_wallet, get_balance, change_balance, cancel_transaction

from app.exceptions import ServiceError


class ActionLimits:
  """
  Класс для хранения лимитов на операции
  """
  CREATION = Decimal('10_000_000.00')
  DEPOSIT = Decimal('1_000_000.00')


def execute_wallet(db: Session, initial_balance: Decimal=Decimal('0')) -> dict[str, str | UUID | Decimal | datetime]:

    if initial_balance < 0:
        raise ServiceError(err_message='Начальный баланс не может быть отрицательным')
    if initial_balance > ActionLimits.CREATION:
        raise ServiceError(err_message=f'Начальный баланс не может превышать лимит в {ActionLimits.CREATION/1_000_000} миллионов')
    wallet = create_wallet(db, initial_balance)

    db.commit()
    db.refresh(wallet)

    return {
        'status': 'New wallet created',
        'wallet_uuid': wallet.uuid,
        'balance': wallet.balance,
        'created_at': wallet.created_at
    }


def execute_balance(db: Session, wallet_uuid: UUID) -> dict[str, str | UUID | Decimal]:

    wallet = get_balance(db, wallet_uuid)

    return {
        'status': 'Wallet balance',
        'wallet_uuid': wallet.uuid,
        'current_balance': wallet.balance
    }


def execute_deposit(db: Session, wallet_uuid: UUID, amount: Decimal) -> dict[str, int | str | UUID | Decimal]:
    """
    Сервис для зачисления средств.
    Бизнес-логика: amount должен быть строго положительным.
    """
    if amount <= 0:
        raise ServiceError(err_message='Для зачисления amount должен быть строго положительным')
    if amount > ActionLimits.DEPOSIT:
        raise ServiceError(err_message=f'Сумма зачисления не может превышать лимит в {ActionLimits.DEPOSIT/1_000_000} миллион')


    trans = change_balance(db, wallet_uuid, amount)

    db.commit()
    db.refresh(trans)

    return {
        'status': 'Deposit completed',
        'transaction_id': trans.id,
        'wallet_uuid': trans.wallet.uuid,
        'amount': trans.amount,
        'balance_after': trans.wallet.balance
    }


def execute_payment(db: Session, wallet_uuid: UUID, amount: Decimal) -> dict[str, int | str | UUID | Decimal]:
    """
    Сервис для списания средств.
    Бизнес-логика: amount должен быть строго отрицательным.
    """
    if amount >= 0:
        raise ServiceError(err_message='Для списания amount должен быть строго отрицательным')
    if abs(amount) > ActionLimits.DEPOSIT:
        raise ServiceError(err_message=f'Сумма списания amount не может превышать лимит в {ActionLimits.DEPOSIT/1_000_000} миллион')

    trans = change_balance(db, wallet_uuid, amount)

    # Коммит делаем здесь: операция прошла все бизнес-проверки
    db.commit()
    db.refresh(trans)

    return {
        'status': 'Withdraw completed',
        'transaction_id': trans.id,
        'wallet_uuid': trans.wallet.uuid,
        'amount': trans.amount,
        'balance_after': trans.wallet.balance
    }


# def execute_cancel(db: Session, transaction_id: int, current_user_uuid: str | None = None) -> dict:
def execute_cancel(db: Session, wallet_uuid: UUID) -> dict[str, str | int | UUID | Decimal]:
    """
    Сервис для отмены транзакции.

    Сейчас — базовая реализация с коммитом.
    """
    # Пример простой проверки прав (если у Wallet есть owner_uuid):
    # wallet, transact = cancel_transaction(db, transaction_id)
    # if wallet.owner_uuid != current_user_uuid:
    #     raise PermissionError("Вы не можете отменять чужие транзакции")

    trans = cancel_transaction(db, wallet_uuid)

    db.commit()
    db.refresh(trans.wallet)

    return {
        'status': 'Cancel completed',
        'transaction_id': trans.id,
        'wallet_uuid': trans.wallet.uuid,
        'reversed_amount': trans.amount,
        'balance_after': trans.wallet.balance
    }