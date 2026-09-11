from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.schemas import (CreateRequest, CreateResponse, BalanceResponse, TransactionRequest, TransactionResponse, CancelResponse)
from app.services import execute_wallet, execute_balance, execute_deposit, execute_payment, execute_cancel, execute_clean

app = FastAPI(title='Wallet Service')
api_v1 = APIRouter(prefix='/api/v1')


@api_v1.post('/wallet', response_model=CreateResponse)
def create_wallet(wallet_data: CreateRequest, db: Session = Depends(get_db)) -> dict[str, str | Decimal]:
    try:
        return execute_wallet(db, wallet_data.balance)
    except ValueError as err_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )


@api_v1.get('/wallets/{wallet_uuid}/balance', response_model=BalanceResponse)
def get_balance(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | Decimal]:
    try:
        return execute_balance(db, wallet_uuid)
    except ValueError as err_code:
        # Кошелёк не найден
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err_code),
        )


@api_v1.post('/wallets/{wallet_uuid}/deposit', response_model=TransactionResponse)
def create_deposit(wallet_uuid: UUID, payload: TransactionRequest, db: Session = Depends(get_db)):
    """
        Зачисление средств: amount должен быть положительным.
        Пример body: {'amount': 500.00}
    """
    try:
        return execute_deposit(db, wallet_uuid, payload.amount)
    except ValueError as err_code:
        # Бизнес-ошибки (неверный знак и т.п.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )


@api_v1.post('/wallets/{wallet_uuid}/payment', response_model=TransactionResponse)
def create_payment(wallet_uuid: UUID, payload: TransactionRequest, db: Session = Depends(get_db)):
    """
        Списание средств: amount должен быть отрицательным.
        Пример body: {'amount': -200.00}
    """
    try:
        return execute_payment(db, wallet_uuid, payload.amount)
    except ValueError as err_code:
        # Бизнес-ошибки (неверный знак, недостаточно средств и т.п.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )


@api_v1.post('/wallets/{wallet_uuid}/cancel', response_model=CancelResponse)
def cancel_transaction(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | int | UUID | Decimal]:
    """
    Отмена последней транзакции для кошелька.
    """
    try:
        return execute_cancel(db, wallet_uuid)
    except ValueError as err_code:
        # Транзакция не найдена и т.п.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err_code),
        )
    except Exception:
        # Неожиданные ошибки (например, проблемы с блокировками)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )

@api_v1.post('/reset_db')
# def reset_database(db: Session = Depends(get_db), include_in_schema=False) -> dict[str, str]:
def reset_database(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        return execute_clean(db)
    except Exception:
        # Неожиданные ошибки
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )

app.include_router(api_v1)