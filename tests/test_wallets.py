# import pytest
# from fastapi import status

from decimal import Decimal
import concurrent.futures
from functools import partial

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Wallet


# ----------- Тесты -----------
def test_create_wallet(client: TestClient, db_session: Session) -> None:
    response = client.post(
        url='/api/v1/wallet',
        json={"balance": "50.00"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'New wallet created'
    assert 'wallet_uuid' in data
    assert data['balance'] == '50.00'


def test_get_balance(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.get(f'/api/v1/wallets/{uuid}/balance')

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Wallet balance'
    assert data['wallet_uuid'] == str(uuid)
    assert data['current_balance'] == '100.00'


def test_deposit(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "30.00"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Deposit completed'
    assert isinstance(data['transaction_id'], int)
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '30.00'
    assert data['balance_after'] == '130.00'


def test_payment_success(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid
    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-40.00"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Withdraw completed'
    assert isinstance(data['transaction_id'], int)
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '-40.00'
    assert data['balance_after'] == '60.00'


def test_payment_insufficient_funds(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid
    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-200.00"}
    )

    assert response.status_code == 400
    assert 'Недостаточно средств для операции' in response.text


def test_payment_invalid_sign(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid
    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "50.00"}
    )

    assert response.status_code == 400
    assert 'Для списания amount должен быть строго отрицательным' in response.text


def test_deposit_invalid_sign(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid
    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "-50.00"}
    )

    assert response.status_code == 400
    assert 'Для зачисления amount должен быть строго положительным' in response.text


def test_cancel_transaction(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    # 1. Создаём депозит
    deposit_response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "70.00"}
    )
    assert deposit_response.status_code == 200
    trans_id = deposit_response.json()['transaction_id']

    # 2. Отменяем транзакцию
    deposit_response = client.post(url=f'/api/v1/transactions/{trans_id}/cancel')

    assert deposit_response.status_code == 200
    data = deposit_response.json()

    assert data['status'] == 'Cancel completed'
    assert type(data['transaction_id']) is int
    assert data['wallet_uuid'] == str(uuid)
    assert data['balance_after'] == '100.00'
    assert data['reversed_amount'] == '70.00'

    # 3. Повторная отмена – транзакция удалена, 404
    cancel_again = client.post(url=f'/api/v1/transactions/{trans_id}/cancel')
    assert cancel_again.status_code == 404

# ----------- Вспомогательные функции (для конкурентных тестов -----------
# Списание средств
def make_withdraw(client: TestClient, wallet_uuid, amount):
    return client.post(
        url=f'/api/v1/wallets/{wallet_uuid}/payment',
        json={"amount": str(amount)}
    )

# Зачисление средств
def make_deposit(client: TestClient, wallet_uuid, amount):
    return client.post(
        url=f'/api/v1/wallets/{wallet_uuid}/deposit',
        json={"amount": str(amount)}
    )

# ----------- Конкурентные тесты -----------
def test_concurrent_withdrawals(client: TestClient, create_wallet: partial) -> None:
    wallet = create_wallet(Decimal("100"))
    uuid = wallet.uuid

    # Фиксируем client и uuid, оставляем только amount
    withdraw = partial(make_withdraw, client, uuid, -60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        first_worker = executor.submit(withdraw)
        second_worker = executor.submit(withdraw)

        first_result, second_result = first_worker.result(), second_worker.result()

    statuses = {first_result.status_code, second_result.status_code}
    assert statuses == {200, 400}  # один успех, одна ошибка

    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '40.00'


def test_concurrent_deposit_and_withdraw(client: TestClient, create_wallet: partial) -> None:
    wallet = create_wallet(Decimal("50"))
    uuid = wallet.uuid

    deposit = partial(make_deposit, client, uuid, 30)
    withdraw= partial(make_withdraw, client, uuid, -40)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        deposit_worker = executor.submit(deposit)
        payment_worker = executor.submit(withdraw)
        deposit_result, payment_result = deposit_worker.result(), payment_worker.result()

    statuses = {deposit_result.status_code, payment_result.status_code}
    assert statuses == {200}  # оба успешны

    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '40.00'