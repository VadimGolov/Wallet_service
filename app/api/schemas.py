from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
        """
        Тело ответа при ошибке.
        """
        detail: str   # Стандартная схема в FastAPI

class CreateRequest(BaseModel):
        """
        Данные от клиента при создании кошелька
        """
        balance: Decimal = Field(default=Decimal('0'), examples=[Decimal('100.00')])

class CreateResponse(BaseModel):
        """
        Данные для клиента после создания кошелька
        """
        status: str = Field(examples=['Wallet created'])
        wallet_uuid: UUID = Field(examples=['3fa85f64-5717-4562-b3fc-2c963f66afa6'])
        balance: Decimal = Field(examples=[Decimal('100.00')])
        created_at: datetime = Field(examples=['2026-10-06T12:00:00Z'])

class BalanceResponse(BaseModel):
        """
        Данные для клиента при получении баланса
        """
        status: str = Field(examples=['Wallet balance'])
        wallet_uuid: UUID = Field(examples=['3fa85f64-5717-4562-b3fc-2c963f66afa6'])
        current_balance: Decimal = Field(examples=[Decimal('100.00')])

class TransactionRequest(BaseModel):
        """
        Данные от клиента при изменении баланса
        """
        amount: Decimal = Field(examples=[Decimal('50.00')])

class TransactionResponse(BaseModel):
        """
        Данные для клиента после изменения баланса
        """
        status: str = Field(examples=['Transaction completed'])
        transaction_id: int = Field(examples=[1])
        wallet_uuid: UUID = Field(examples=['3fa85f64-5717-4562-b3fc-2c963f66afa6'])
        amount: Decimal = Field(examples=[Decimal('50.00')])
        balance_after: Decimal = Field(examples=[Decimal('150.00')])

class CancelResponse(BaseModel):
        """
        Данные для клиента после отмены операции
        """
        status: str = Field(examples=['Transaction cancelled'])
        transaction_id: int = Field(examples=[1])
        wallet_uuid: UUID = Field(examples=['3fa85f64-5717-4562-b3fc-2c963f66afa6'])
        reversed_amount: Decimal = Field(examples=[Decimal('50.00')])
        balance_after: Decimal = Field(examples=[Decimal('100.00')])

class DeleteResponse(BaseModel):
        """
        Данные для клиента после удаления кошелька
        """
        status: str = Field(examples=['Deletion completed'])
        deleted_wallet_uuid: UUID = Field(examples=['3fa85f64-5717-4562-b3fc-2c963f66afa6'])