from uuid import UUID

import concurrent.futures
from functools import partial
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Wallet, Transaction


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

    # Проверяем, что транзакция не создалось (не должна создаваться при создании кошелька)
    wallet_uuid = UUID(data['wallet_uuid'])
    transactions = db_session.query(Transaction).filter(Transaction.wallet_uuid == wallet_uuid).all()

    assert len(transactions) == 0


def test_get_balance(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.get(url=f'/api/v1/wallets/{uuid}/balance')

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Wallet balance'
    assert data['wallet_uuid'] == str(uuid)
    assert data['current_balance'] == '100.00'


def test_deposit(client: TestClient, wallet: Wallet | None, db_session: Session) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "30.00"}
    )

    assert response.status_code == 200
    data = response.json()

    print(data)

    assert data['status'] == 'Deposit completed'
    assert isinstance(data['transaction_id'], int)
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '30.00'
    assert data['balance_after'] == '130.00'

    # Проверяем, что транзакция создалась
    transactions = db_session.query(Transaction).filter(Transaction.wallet_uuid == uuid).all()

    assert len(transactions) == 1


def test_payment_success(client: TestClient, wallet: Wallet | None, db_session: Session) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-60.00"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Withdraw completed'
    assert isinstance(data['transaction_id'], int)
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '-60.00'
    assert data['balance_after'] == '40.00'

    # Проверяем, что транзакция создалась
    transactions = db_session.query(Transaction).filter(Transaction.wallet_uuid == uuid).all()

    assert len(transactions) == 1


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

    # 2. Отменяем транзакцию
    deposit_response = client.post(url=f'/api/v1/wallets/{uuid}/cancel')

    assert deposit_response.status_code == 200
    data = deposit_response.json()

    assert data['status'] == 'Cancel completed'
    assert type(data['transaction_id']) is int
    assert data['wallet_uuid'] == str(uuid)
    assert data['reversed_amount'] == '70.00'
    assert data['balance_after'] == '100.00'

    # 3. Повторная отмена – транзакция отменена, 404
    cancel_again = client.post(url=f'/api/v1/wallets/{uuid}/cancel')

    assert cancel_again.status_code == 404

# ----------- Вспомогательные функции (для конкурентных тестов -----------
# Создание кошелька
def concurrent_wallet(client: TestClient):
    return client.post(
        url='/api/v1/wallet',
        json={"balance": "100.00"}
    )

# Списание средств
def make_withdraw(client: TestClient, wallet_uuid, amount):
    return client.post(
        url=f'/api/v1/wallets/{wallet_uuid}/payment',
        json={"amount": str(amount)}
    )

# Зачисление средств
def make_deposit(client: TestClient, wallet_uuid: UUID, amount):
    return client.post(
        url=f'/api/v1/wallets/{wallet_uuid}/deposit',
        json={"amount": str(amount)}
    )

# ----------- Конкурентные тесты -----------
def test_concurrent_withdraws(con_client: TestClient) -> None:
    # Создаём кошелёк с балансом 100
    new_wallet = concurrent_wallet(con_client)
    assert new_wallet is not None, 'We could not create a wallet via post request'

    wallet_data = new_wallet.json()
    uuid = UUID(wallet_data['wallet_uuid'])

    # Фиксируем client и uuid, оставляем только amount
    max_withdraw = partial(make_withdraw, con_client, uuid, -60)
    min_withdraw = partial(make_withdraw, con_client, uuid, -15)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        first_worker = executor.submit(max_withdraw)
        second_worker = executor.submit(min_withdraw)
        third_worker = executor.submit(min_withdraw)
        fourth_worker = executor.submit(max_withdraw)

        first_res = first_worker.result()
        second_res = second_worker.result()
        third_res = third_worker.result()
        fourth_res = fourth_worker.result()

    common_states = {first_res.status_code, second_res.status_code, third_res.status_code, fourth_res.status_code}
    assert common_states == {200, 400}  # один успех, одна ошибка

    balance = con_client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '10.00'


def test_concurrent_deposit_and_withdraw(con_client: TestClient) -> None:
    # Создаём кошелёк с балансом 100
    new_wallet = concurrent_wallet(con_client)
    assert new_wallet is not None, 'We could not create a wallet via post request'

    wallet_data = new_wallet.json()
    uuid = UUID(wallet_data['wallet_uuid'])

    # Фиксируем client и uuid, оставляем только amount
    deposit = partial(make_deposit, con_client, uuid, 30)
    withdraw = partial(make_withdraw, con_client, uuid, -60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        first_dt_worker = executor.submit(deposit)
        first_wd_worker = executor.submit(withdraw)
        second_dt_worker = executor.submit(deposit)
        third_dt_worker = executor.submit(withdraw)

    first_res = first_dt_worker.result()
    second_res = first_wd_worker.result()
    third_res = second_dt_worker.result()
    fourth_res = third_dt_worker.result()

    common_states = {first_res.status_code, second_res.status_code, third_res.status_code, fourth_res.status_code}
    assert common_states == {200}  # все успех

    balance = con_client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '40.00'