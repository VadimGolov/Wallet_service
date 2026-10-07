from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from app.configs.limits import ActionLimits
from app.db.models import Transaction, Wallet
from app.exceptions.catalog import ServiceError, WalletError
from app.services.repository import create_wallet, delete_wallet, get_balance, change_balance, cancel_transaction


def execute_wallet(db: Session, initial_balance: Decimal = Decimal('0')) -> dict[str, str | UUID | Decimal | datetime]:

    if initial_balance < 0:
        raise ServiceError(WalletError.NEGATIVE_BALANCE)
    if initial_balance > ActionLimits.CREATION:
        raise ServiceError(WalletError.BALANCE_LIMIT)

    wallet: Wallet = create_wallet(db, initial_balance)
    db.commit()
    db.refresh(wallet)

    return {
        'status': 'New wallet created',
        'wallet_uuid': wallet.uuid,
        'balance': wallet.balance,
        'created_at': wallet.created_at,
    }


def execute_delete(db: Session, wallet_uuid: UUID) -> dict[str, str | UUID]:
    delete_wallet(db, wallet_uuid)
    db.commit()

    return {
        'status': 'Deletion completed',
        'deleted_wallet_uuid': wallet_uuid,
    }


def execute_balance(db: Session, wallet_uuid: UUID) -> dict[str, str | UUID | Decimal]:
    wallet: Wallet = get_balance(db, wallet_uuid)

    return {
        'status': 'Wallet balance',
        'wallet_uuid': wallet_uuid,
        'current_balance': wallet.balance,
    }


def execute_deposit(db: Session, wallet_uuid: UUID, amount: Decimal) -> dict[str, int | str | UUID | Decimal]:
    """
    Зачисление средств — amount должен быть строго положительным.
    """
    if amount <= 0:
        raise ServiceError(WalletError.AMOUNT_MUST_BE_POSITIVE)
    if amount > ActionLimits.DEPOSIT:
        raise ServiceError(WalletError.DEPOSIT_LIMIT)

    trans: Transaction = change_balance(db, wallet_uuid, amount)
    db.commit()
    db.refresh(trans)

    return {
        'status': 'Deposit completed',
        'transaction_id': trans.id,
        'wallet_uuid': wallet_uuid,
        'amount': amount,
        'balance_after': trans.wallet.balance,
    }


def execute_payment(db: Session, wallet_uuid: UUID, amount: Decimal) -> dict[str, int | str | UUID | Decimal]:
    """
    Списание средств — amount должен быть строго отрицательным.
    """
    if amount >= 0:
        raise ServiceError(WalletError.AMOUNT_MUST_BE_NEGATIVE)
    if abs(amount) > ActionLimits.WITHDRAW:
        raise ServiceError(WalletError.WITHDRAW_LIMIT)

    trans: Transaction = change_balance(db, wallet_uuid, amount)
    db.commit()
    db.refresh(trans)

    return {
        'status': 'Withdraw completed',
        'transaction_id': trans.id,
        'wallet_uuid': wallet_uuid,
        'amount': amount,
        'balance_after': trans.wallet.balance,
    }


def execute_cancel(db: Session, wallet_uuid: UUID) -> dict[str, str | int | UUID | Decimal]:
    """
    Отмена последней транзакции для кошелька.
    """
    trans: Transaction = cancel_transaction(db, wallet_uuid)
    db.commit()
    db.refresh(trans.wallet)

    return {
        'status': 'Cancel completed',
        'transaction_id': trans.id,
        'wallet_uuid': wallet_uuid,
        'reversed_amount': trans.amount,
        'balance_after': trans.wallet.balance,
    }