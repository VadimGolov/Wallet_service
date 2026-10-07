from decimal import Decimal

class ActionLimits:
    """
    Класс для хранения лимитов на операции.
    """
    CREATION = Decimal('10_000_000')
    DEPOSIT = Decimal('1_000_000')
    WITHDRAW = Decimal('1_000_000')