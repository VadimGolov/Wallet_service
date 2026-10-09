from typing import Final
from decimal import Decimal

class ActionLimits:
    """
    Класс для хранения лимитов на операции.
    """
    CREATION: Final[Decimal] = Decimal('10_000_000')
    DEPOSIT: Final[Decimal] = Decimal('1_000_000')
    WITHDRAW: Final[Decimal] = Decimal('1_000_000')