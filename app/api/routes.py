from uuid import UUID
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import (
    CreateRequest, CreateResponse, DeleteResponse, BalanceResponse,
    TransactionRequest, TransactionResponse, CancelResponse
)
from app.api.session import get_db
from app.exceptions.responses import (
    CREATE_RESPONSES, DELETE_RESPONSES, BALANCE_RESPONSES,
    DEPOSIT_RESPONSES, PAYMENT_RESPONSES, CANCEL_RESPONSES
)
from app.services.actions import (
    execute_wallet, execute_delete, execute_balance,
    execute_deposit, execute_payment, execute_cancel
)


api_v1 = APIRouter(prefix='/api/v1')


@api_v1.post('/wallet', response_model=CreateResponse, responses=CREATE_RESPONSES)
def create_wallet(wallet_data: CreateRequest, db: Session = Depends(get_db)) -> dict[str, str | UUID | Decimal | datetime]:
    """
    Создание кошелька
    """
    return execute_wallet(db, wallet_data.balance)


@api_v1.post('/wallets/{wallet_uuid}/delete', response_model=DeleteResponse, responses=DELETE_RESPONSES)
def delete_wallet(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | UUID]:
    """
    Удаление кошелька
    """
    return execute_delete(db, wallet_uuid)


@api_v1.get('/wallets/{wallet_uuid}/balance', response_model=BalanceResponse, responses=BALANCE_RESPONSES)
def get_balance(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | UUID | Decimal]:
    """
    Получение баланса
    """
    return execute_balance(db, wallet_uuid)


@api_v1.post('/wallets/{wallet_uuid}/deposit', response_model=TransactionResponse, responses=DEPOSIT_RESPONSES)
def create_deposit(wallet_uuid: UUID, transaction: TransactionRequest, db: Session = Depends(get_db)) -> dict[str, int | str | UUID | Decimal]:
    """
    Зачисление средств: amount должен быть положительным
    """
    return execute_deposit(db, wallet_uuid, transaction.amount)


@api_v1.post('/wallets/{wallet_uuid}/payment', response_model=TransactionResponse, responses=PAYMENT_RESPONSES)
def create_payment(wallet_uuid: UUID, transaction: TransactionRequest, db: Session = Depends(get_db)) -> dict[str, int | str | UUID | Decimal]:
    """
    Списание средств: amount должен быть отрицательным
    """
    return execute_payment(db, wallet_uuid, transaction.amount)


@api_v1.post('/wallets/{wallet_uuid}/cancel', response_model=CancelResponse, responses=CANCEL_RESPONSES)
def cancel_transaction(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | int | UUID | Decimal]:
    """
    Отмена последней транзакции
    """
    return execute_cancel(db, wallet_uuid)