"""
Контракт ошибок API: каталоги ошибок, и сервисное исключение
"""
from enum import Enum
from uuid import UUID

from fastapi import status

from app.configs.limits import ActionLimits


# Каталоги ошибок
class WalletError(Enum):
    """
    Бизнес-ошибки сервиса.
    """
    WALLET_NOT_FOUND = ('Кошелёк <uuid> не найден', status.HTTP_404_NOT_FOUND)
    NO_TRANSACTIONS = ('У кошелька <uuid> нет транзакций', status.HTTP_404_NOT_FOUND)
    ALREADY_CANCELLED = ('Последняя транзакция для кошелька <uuid> уже была отменена', status.HTTP_404_NOT_FOUND)
    NEGATIVE_BALANCE = ('Начальный баланс не может быть отрицательным', status.HTTP_400_BAD_REQUEST)
    BALANCE_LIMIT = (f'Начальный баланс не может превышать лимит в {ActionLimits.CREATION//1_000_000} миллионов', status.HTTP_400_BAD_REQUEST, )
    NON_ZERO_BALANCE = ('Для удаления кошелька баланс должен быть нулевым', status.HTTP_400_BAD_REQUEST)
    AMOUNT_MUST_BE_POSITIVE = ('Для зачисление сумма должна быть строго положительной', status.HTTP_400_BAD_REQUEST)
    AMOUNT_MUST_BE_NEGATIVE = ('Для списания сумма должна быть строго отрицательной', status.HTTP_400_BAD_REQUEST)
    DEPOSIT_LIMIT = (f'Сумма зачисления не может превышать лимит в {ActionLimits.DEPOSIT//1_000_000} миллион', status.HTTP_400_BAD_REQUEST)
    WITHDRAW_LIMIT = (f'Сумма списания не может превышать лимит в {ActionLimits.WITHDRAW//1_000_000} миллион', status.HTTP_400_BAD_REQUEST)
    INSUFFICIENT_FUNDS = ('Недостаточно средств для списания', status.HTTP_400_BAD_REQUEST)


class CommonError(Enum):
    """
    Инфраструктурные категории ошибок.
    (Кортежи для единообразия с WalletError)
    """
    VALIDATION_ERROR = ('Отправленные данные не прошли проверку', status.HTTP_422_UNPROCESSABLE_CONTENT)
    INTERNAL = ('Внутренняя ошибка сервера', status.HTTP_500_INTERNAL_SERVER_ERROR)


# Сервисное исключение
class ServiceError(ValueError):
    """
    Ошибки бизнес-логики сервиса
    класс WalletError
    """
    def __init__(self, error: WalletError, uuid: UUID | None = None):
        message = error.value[0]
        if uuid is not None:
            message = message.replace('<uuid>', str(uuid))
        super().__init__(message)
        self.status_code = error.value[1]