from fastapi import status

from app.api.schemas import ErrorResponse
from app.exceptions.catalog import CommonError, WalletError


# Общий слой
COMMON_RESPONSES = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        'model': ErrorResponse,
        'description': CommonError.VALIDATION_ERROR.value[0],
        'content': {
            'application/json': {
                'example': {'detail': CommonError.VALIDATION_ERROR.value[0]},
            },
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        'model': ErrorResponse,
        'description': CommonError.INTERNAL.value[0],
        'content': {
            'application/json': {
                'example': {'detail': CommonError.INTERNAL.value[0]},
            },
        },
    },
}


# Специфичные слои
CREATE_SPECIFIC = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': '  \n'.join([
            WalletError.NEGATIVE_BALANCE.value[0],
            WalletError.BALANCE_LIMIT.value[0],
        ]),
        'content': {
            'application/json': {
                'examples': {
                    'negative_balance': {
                        'summary': 'Отрицательный баланс',
                        'value': {'detail': WalletError.NEGATIVE_BALANCE.value[0]},
                    },
                    'balance_limit': {
                        'summary': 'Превышен лимит',
                        'value': {'detail': WalletError.BALANCE_LIMIT.value[0]},
                    },
                },
            },
        },
    },
}

DELETE_SPECIFIC = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': WalletError.NON_ZERO_BALANCE.value[0],
        'content': {
            'application/json': {
                'example': {'detail': WalletError.NON_ZERO_BALANCE.value[0]},
            },
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': WalletError.WALLET_NOT_FOUND.value[0],
        'content': {
            'application/json': {
                'example': {'detail': 'Кошелёк 3fa85f64-5717-4562-b3fc-2c963f66afa6 не найден'},
            },
        },
    },
}

BALANCE_SPECIFIC = {
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': WalletError.WALLET_NOT_FOUND.value[0],
        'content': {
            'application/json': {
                'example': {'detail': 'Кошелёк 3fa85f64-5717-4562-b3fc-2c963f66afa6 не найден'},
            },
        },
    },
}

DEPOSIT_SPECIFIC = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': '  \n'.join([
            WalletError.AMOUNT_MUST_BE_POSITIVE.value[0],
            WalletError.DEPOSIT_LIMIT.value[0],
        ]),
        'content': {
            'application/json': {
                'examples': {
                    'amount_must_be_positive': {
                        'summary': 'Сумма должна быть положительной',
                        'value': {'detail': WalletError.AMOUNT_MUST_BE_POSITIVE.value[0]},
                    },
                    'deposit_limit': {
                        'summary': 'Превышен лимит зачисления',
                        'value': {'detail': WalletError.DEPOSIT_LIMIT.value[0]},
                    },
                },
            },
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': WalletError.WALLET_NOT_FOUND.value[0],
        'content': {
            'application/json': {
                'example': {'detail': 'Кошелёк 3fa85f64-5717-4562-b3fc-2c963f66afa6 не найден'},
            },
        },
    },
}

PAYMENT_SPECIFIC = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': '  \n'.join([
            WalletError.INSUFFICIENT_FUNDS.value[0],
            WalletError.AMOUNT_MUST_BE_NEGATIVE.value[0],
            WalletError.WITHDRAW_LIMIT.value[0],
        ]),
        'content': {
            'application/json': {
                'examples': {
                    'insufficient_funds': {
                        'summary': 'Недостаточно средств',
                        'value': {'detail': WalletError.INSUFFICIENT_FUNDS.value[0]},
                    },
                    'amount_must_be_negative': {
                        'summary': 'Сумма должна быть отрицательной',
                        'value': {'detail': WalletError.AMOUNT_MUST_BE_NEGATIVE.value[0]},
                    },
                    'withdraw_limit': {
                        'summary': 'Превышен лимит списания',
                        'value': {'detail': WalletError.WITHDRAW_LIMIT.value[0]},
                    },
                },
            },
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': WalletError.WALLET_NOT_FOUND.value[0],
        'content': {
            'application/json': {
                'example': {'detail': 'Кошелёк 3fa85f64-5717-4562-b3fc-2c963f66afa6 не найден'},
            },
        },
    },
}

CANCEL_SPECIFIC = {
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': '  \n'.join([
            WalletError.WALLET_NOT_FOUND.value[0],
            WalletError.NO_TRANSACTIONS.value[0],
            WalletError.ALREADY_CANCELLED.value[0],
        ]),
        'content': {
            'application/json': {
                'examples': {
                    'wallet_not_found': {
                        'summary': 'Кошелёк не найден',
                        'value': {'detail': 'Кошелёк 3fa85f64-5717-4562-b3fc-2c963f66afa6 не найден'},
                    },
                    'no_transactions': {
                        'summary': 'Нет транзакций',
                        'value': {'detail': 'У кошелька 3fa85f64-5717-4562-b3fc-2c963f66afa6 нет транзакций'},
                    },
                    'already_cancelled': {
                        'summary': 'Уже отменена',
                        'value': {'detail': 'Последняя транзакция для кошелька 3fa85f64-5717-4562-b3fc-2c963f66afa6 уже была отменена'},
                    },
                },
            },
        },
    },
}


# Итоговые наборы для декораторов
CREATE_RESPONSES = COMMON_RESPONSES | CREATE_SPECIFIC
DELETE_RESPONSES = COMMON_RESPONSES | DELETE_SPECIFIC
BALANCE_RESPONSES = COMMON_RESPONSES | BALANCE_SPECIFIC
DEPOSIT_RESPONSES = COMMON_RESPONSES | DEPOSIT_SPECIFIC
PAYMENT_RESPONSES = COMMON_RESPONSES | PAYMENT_SPECIFIC
CANCEL_RESPONSES = COMMON_RESPONSES | CANCEL_SPECIFIC