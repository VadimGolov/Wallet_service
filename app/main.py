from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db  # твоя зависимость для сессии (Session)
from app.schemas import WalletCreate
from app.services import execute_wallet, execute_balance, execute_deposit, execute_payment, execute_cancel

app = FastAPI(title='Wallet Service')
api_v1 = APIRouter(prefix='/api/v1')

@api_v1.post('/wallet')
def create_wallet(wallet_data: WalletCreate, db: Session = Depends(get_db)) -> dict[str, str | Decimal]:
    try:
        return execute_wallet(db, wallet_data.balance)
    except ValueError as err_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )

@api_v1.get('/wallets/{wallet_uuid}/balance')
def get_balance(wallet_uuid: str, db: Session = Depends(get_db)) -> dict[str, str | Decimal]:
    try:
        result = execute_balance(db, wallet_uuid)
        return result
    except ValueError as err_code:
        # Кошелёк не найден
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err_code),
        )

@api_v1.post('/wallets/{wallet_uuid}/payment')
def create_payment(wallet_uuid: str, amount: Decimal, db: Session = Depends(get_db)) -> dict[str, int | str | Decimal]:
    """
    Списание средств: amount должен быть отрицательным.
    Пример body: {'amount': -100.00}
    """
    try:
        result = execute_payment(db, wallet_uuid, amount)
        return result
    except ValueError as err_code:
        # Бизнес-ошибки (неверный знак, недостаточно средств и т.п.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )


@api_v1.post('/wallets/{wallet_uuid}/deposit')
def create_deposit(wallet_uuid: str, amount: Decimal, db: Session = Depends(get_db)) -> dict[str, int | str | Decimal]:
    """
    Зачисление средств: amount должен быть положительным.
    Пример body: {'amount': 500.00}
    """
    try:
        result = execute_deposit(db, wallet_uuid, amount)
        return result
    except ValueError as err_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err_code),
        )


@api_v1.post('/transactions/{transaction_id}/cancel')
def cancel_transaction(transaction_id: int, db: Session = Depends(get_db)) -> dict[str, str | int | Decimal]:
    """
    Отмена одной транзакции по ID.
    Атомарно: либо всё, либо ничего.
    """
    try:
        result = execute_cancel(db, transaction_id)
        return result
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
        result = reset_database(db)
        return result
    except Exception:
        # Неожиданные ошибки
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса",
        )

app.include_router(api_v1)