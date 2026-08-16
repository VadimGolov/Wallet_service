from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime


class WalletCreate(BaseModel):
    """
    Данные от клиента при создании кошелька
    """
    uuid: str  # клиент сам присылает UUID, либо генерирует сервис
    balance: Decimal = Decimal('0')  # по умолчанию в БД будет 0.00


class WalletResponse(BaseModel):
    """
    Данные для клиента после создания/получения
    """
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    balance: Decimal
    created_at: datetime


class TransactionCreate(BaseModel):
    """
    Данные от клиента при изменении баланса
    """
    wallet_uuid: str
    amount: Decimal  # положительное или отрицательное значение


class TransactionResponse(BaseModel):
    """
    Данные для клиента после изменения баланса
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_uuid: str
    amount: Decimal
    created_at: datetime