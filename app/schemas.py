from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class CreateRequest(BaseModel):
    """
    Данные от клиента при создании кошелька
    """
    balance: Decimal = Decimal('0')  # по умолчанию в БД будет 0.00


class CreateResponse(BaseModel):
    """
    Данные для клиента после создания
    """
    status: str
    wallet_uuid: UUID
    balance: Decimal
    created_at: datetime


class BalanceRequest(BaseModel):
    """
    Данные от клиента при получении баланса
    """
    wallet_uuid: UUID


class BalanceResponse(BaseModel):
    """
    Данные для клиента при получении баланса
    """
    status: str
    wallet_uuid: UUID
    balance: Decimal


class TransactionRequest(BaseModel):
    """
    Данные от клиента при изменении баланса
    """
    wallet_uuid: UUID
    amount: Decimal  # положительное или отрицательное значение


class TransactionResponse(BaseModel):
    """
    Данные для клиента после изменения баланса
    """
    status: str
    transaction_id: int
    wallet_uuid: UUID
    amount: Decimal
    balance_after: Decimal

class CancelRequest(BaseModel):
    """
    Данные от клиента для отмены операции
    """
    transaction_id: int

class CancelResponse(BaseModel):
    """
    Данные для клиента после отмены операции
    """
    status: str
    transaction_id: int
    wallet_uuid: UUID
    reversed_amount: Decimal
    balance_after: Decimal