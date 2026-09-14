from uuid import UUID
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ServiceError
from app.schemas import CreateRequest, CreateResponse, BalanceResponse, TransactionRequest, TransactionResponse, CancelResponse
from app.services import execute_wallet, execute_balance, execute_deposit, execute_payment, execute_cancel

app = FastAPI(title='Wallet Service')
api_v1 = APIRouter(prefix='/api/v1')


@api_v1.post('/wallet', response_model=CreateResponse)
def create_wallet(wallet_data: CreateRequest, db: Session = Depends(get_db)) -> dict[str, str | UUID | Decimal | datetime]:
    """
    Создание нового кошелька.
    """
    try:
        return execute_wallet(db, wallet_data.balance)
    except ServiceError as fault:
        raise HTTPException(
            status_code=fault.status_code,
            detail=str(fault)
        )
    except Exception:
        # Другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )


@api_v1.get('/wallets/{wallet_uuid}/balance', response_model=BalanceResponse)
def get_balance(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str |UUID | Decimal]:
    """
    Получение баланса кошелька.
    """
    try:
        return execute_balance(db, wallet_uuid)
    except ServiceError as fault:
        raise HTTPException(
            status_code=fault.status_code,
            detail=str(fault)
        )
    except Exception:
        # Другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )


@api_v1.post('/wallets/{wallet_uuid}/deposit', response_model=TransactionResponse)
def create_deposit(wallet_uuid: UUID, transaction: TransactionRequest, db: Session = Depends(get_db)) -> dict[str, int | str | UUID | Decimal ]:
    """
        Зачисление средств: amount должен быть положительным.
        Пример body: {"amount": "500.00"}
    """
    try:
        return execute_deposit(db, wallet_uuid, transaction.amount)
    except ServiceError as fault:
        raise HTTPException(
            status_code=fault.status_code,
            detail=str(fault)
        )
    except Exception:
        # Другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )


@api_v1.post('/wallets/{wallet_uuid}/payment', response_model=TransactionResponse)
def create_payment(wallet_uuid: UUID, transaction: TransactionRequest, db: Session = Depends(get_db)) -> dict[str, int | str | UUID | Decimal ]:
    """
        Списание средств: amount должен быть отрицательным.
        Пример body: {"amount": "-200.00"}
    """
    try:
        return execute_payment(db, wallet_uuid, transaction.amount)
    except ServiceError as fault:
        raise HTTPException(
            status_code=fault.status_code,
            detail=str(fault)
        )
    except Exception:
        # Другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )


@api_v1.post('/wallets/{wallet_uuid}/cancel', response_model=CancelResponse)
def cancel_transaction(wallet_uuid: UUID, db: Session = Depends(get_db)) -> dict[str, str | int | UUID | Decimal]:
    """
    Отмена последней транзакции для кошелька.
    """
    try:
        return execute_cancel(db, wallet_uuid)
    except ServiceError as fault:
        raise HTTPException(
            status_code=fault.status_code,
            detail=str(fault)
        )
    except Exception:
        # Другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )


app.include_router(api_v1)