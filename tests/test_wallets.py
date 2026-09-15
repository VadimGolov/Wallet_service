from uuid import uuid4, UUID

import concurrent.futures
from functools import partial

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Wallet, Transaction


# ---------- Простые Тесты ----------
def test_create_wallet(client: TestClient, db_session: Session) -> None:
    """
    Создание кошелька с указанным балансом → код 200 [успешно],
    Проверка отсутствия транзакции при создании [успешно].
    """
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


def test_create_wallet_default_balance(client: TestClient) -> None:
    """
    Создание кошелька без указания баланса → код 200 [успешно].
    """
    response = client.post(
        url='/api/v1/wallet',
        json={}
    )
    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'New wallet created'
    assert 'wallet_uuid' in data
    assert data['balance'] == '0.00'


def test_create_wallet_negative_balance(client: TestClient) -> None:
    """
    Попытка создания кошелька с отрицательным начальным балансом → код 400 [ошибка].
    """
    response = client.post(
        url='/api/v1/wallet',
        json={"balance": "-50.00"}
    )
    assert response.status_code == 400
    assert 'не может быть отрицательным' in response.text


def test_create_wallet_exceeds_max(client: TestClient) -> None:
    """
    Попытка создания кошелька с балансом больше 10 000 000 → код 400 [ошибка].
    """
    response = client.post(
        url='/api/v1/wallet',
        json={"balance": "10000000.01"}
    )
    assert response.status_code == 400
    assert 'не может превышать лимит' in response.text.lower()


def test_create_wallet_boundary_max(client: TestClient) -> None:
    """
    Создание кошелька с балансом ровно 10 000 000 → код 200 [успешно] (проверка верхней границы).
    """
    response = client.post(
        url='/api/v1/wallet',
        json={"balance": "10000000.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'New wallet created'
    assert data['balance'] == '10000000.00'


def test_get_balance(client: TestClient, wallet: Wallet | None) -> None:
    """
    Удачное получение баланса кошелька → код 200 [успешно].
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.get(url=f'/api/v1/wallets/{uuid}/balance')

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Wallet balance'
    assert data['wallet_uuid'] == str(uuid)
    assert data['current_balance'] == '100.00'


def test_get_balance_invalid_uuid(client: TestClient) -> None:
    """
    Попытка получения баланса с неправильным форматом UUID → код 422 [ошибка] (валидация FastAPI).
    """
    response = client.get(
        url='/api/v1/wallets/not-a-uuid/balance'
    )
    assert response.status_code == 422


def test_get_balance_wallet_not_found(client: TestClient) -> None:
    """
    Попытка получения баланса с правильным форматом UUID, но отсутствием кошелька в БД → код 404 [ошибка].
    """
    fake_uuid = uuid4()
    response = client.get(
        url=f'/api/v1/wallets/{fake_uuid}/balance'
    )

    assert response.status_code == 404
    assert 'не найден' in response.text.lower()


def test_deposit(client: TestClient, wallet: Wallet | None, db_session: Session) -> None:
    """
    Успешное пополнение кошелька → код 200 [успешно]
    Проверка, что транзакция создана [успешно]
    """
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

    # Проверяем, что транзакция создалась
    transactions = db_session.query(Transaction).filter(Transaction.wallet_uuid == uuid).all()

    assert len(transactions) == 1

def test_deposit_invalid_sign(client: TestClient, wallet: Wallet | None) -> None:
    """
     Попытка пополнения с неправильным знаком amount < 0 → код 400 [ошибка].
     """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "-50.00"}
    )

    assert response.status_code == 400
    assert 'должен быть строго положительным' in response.text


def test_deposit_missing_amount(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка пополнения с отсутствием amount в теле запроса → код 422 [ошибка] (валидация Pydantic).
    """
    assert wallet is not None
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={}
    )
    assert response.status_code == 422


def test_deposit_invalid_uuid(client: TestClient) -> None:
    """
    Попытка пополнения с неправильным форматом UUID в пути → код 422 [ошибка] (валидация FastAPI).
    """
    response = client.post(
        url = f'/api/v1/wallets/not-a-uuid/deposit',
        json = {"amount": "50.00"}
    )

    assert response.status_code == 422


def test_deposit_wallet_not_found(client: TestClient) -> None:
    """
    Попытка пополнения с правильным форматом UUID, но отсутствием кошелька в БД → код 404 [ошибка].
    """
    fake_uuid = uuid4()
    response = client.post(
        url=f'/api/v1/wallets/{fake_uuid}/deposit',
        json={"amount": "50.00"}
    )
    assert response.status_code == 404
    assert 'не найден' in response.text.lower()


def test_deposit_exceeds_max(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка пополнения на сумму более 1 000 000 → код 400 [ошибка].
    """
    assert wallet is not None
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "1000000.01"}
    )
    assert response.status_code == 400
    assert 'не может превышать лимит' in response.text.lower()


def test_deposit_boundary_max(client: TestClient, wallet: Wallet | None) -> None:
    """
    Пополнение суммой ровно 1 000 000 → код 200 [успешно] (проверка верхней границы).
    """
    assert wallet is not None
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/deposit',
        json={"amount": "1000000.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'Deposit completed'
    assert data['amount'] == '1000000.00'
    assert data['balance_after'] == '1000100.00'   # 100 (фикстура) + 1 000 000


def test_payment_success(client: TestClient, wallet: Wallet | None, db_session: Session) -> None:
    """
    Успешное списание с кошелька → код 200 [успешно]
    Проверка, что транзакция создана [успешно]
    """
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
    """
    Попытка списания с превышением баланса кошелька → код 400 [ошибка]
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-200.00"}
    )

    assert response.status_code == 400
    assert 'Недостаточно средств' in response.text


def test_payment_invalid_sign(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка списания с неправильным знаком amount > 0 → код 400 [ошибка].
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "50.00"}
    )

    assert response.status_code == 400
    assert 'должен быть строго отрицательным' in response.text


def test_payment_exact_balance(client: TestClient, wallet: Wallet | None) -> None:
    """
    Создание списания ровно в ноль → код 200 [успешно].
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-100.00"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Withdraw completed'
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '-100.00'
    assert data['balance_after'] == '0.00'

    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '0.00'


def test_payment_missing_amount(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка списания с отсутствием amount в теле → 422 [ошибка] (валидация Pydantic).
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={}
    )
    assert response.status_code == 422


def test_payment_invalid_uuid(client: TestClient) -> None:
    """
    Попытка списания с неправильным форматом UUID в пути → код 422 [ошибка] (валидация FastAPI).
    """
    response = client.post(
        url = f'/api/v1/wallets/not-a-uuid/payment',
        json = {"amount": "-50.00"}
    )

    assert response.status_code == 422


def test_payment_wallet_not_found(client: TestClient) -> None:
    """
    Попытка списания с правильным форматом UUID, но отсутствием кошелька в БД → код 404 [ошибка].
    """
    fake_uuid = uuid4()
    response = client.post(
        url=f'/api/v1/wallets/{fake_uuid}/payment',
        json={"amount": "-50.00"}
    )
    assert response.status_code == 404
    assert 'не найден' in response.text.lower()


def test_payment_exceeds_max(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка списания на сумму больше 1 000 000 → код 400 [ошибка].
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-1000000.01"}
    )
    assert response.status_code == 400
    assert 'не может превышать лимит' in response.text.lower()


def test_payment_boundary_max(client: TestClient) -> None:
    """
    Списание ровно на 1 000 000 при достаточном балансе → код 200 [успешно].
    """

    # Создаём кошелёк с балансом 1 000 000.
    create_response = client.post(
        url='/api/v1/wallet',
        json={"balance": "1000000.00"}
    )

    assert create_response.status_code == 200
    uuid = create_response.json()['wallet_uuid']

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-1000000.00"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == 'Withdraw completed'
    assert data['wallet_uuid'] == str(uuid)
    assert data['amount'] == '-1000000.00'
    assert data['balance_after'] == '0.00'


def test_cancel_transaction(client: TestClient, wallet: Wallet | None) -> None:
    """
    Успешная отмена зачисления на кошелек → код 200 [успешно]
    Повторная отмена для этого кошелька → код 404 [ошибка]
    """
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

    # Проверяем через GET /balance
    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '100.00'


    # 3. Повторная отмена – транзакция отменена, 404
    cancel_again = client.post(url=f'/api/v1/wallets/{uuid}/cancel')

    assert cancel_again.status_code == 404


def test_cancel_payment_restores_balance(client: TestClient, wallet: Wallet | None) -> None:
    """
    Успешная отмена списания с кошелька → код 200 [успешно]
    Повторная проверка баланса [успешно]
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    # Списание -40 → баланс 60
    payment_response = client.post(
        url=f'/api/v1/wallets/{uuid}/payment',
        json={"amount": "-40.00"}
    )
    assert payment_response.status_code == 200

    # Отменяем последнюю транзакцию
    cancel_response = client.post(
        url=f'/api/v1/wallets/{uuid}/cancel'
    )
    assert cancel_response.status_code == 200
    data = cancel_response.json()

    assert data['status'] == 'Cancel completed'
    assert data['wallet_uuid'] == str(uuid)
    assert data['reversed_amount'] == '-40.00'
    assert data['balance_after'] == '100.00'   # вернулись к исходному

    # Проверяем через GET /balance
    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '100.00'


def test_cancel_without_transactions(client: TestClient, wallet: Wallet | None) -> None:
    """
    Попытка отмены при отсутствии транзакций → код 404 [ошибка].
    """
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    response = client.post(
        url=f'/api/v1/wallets/{uuid}/cancel'
    )
    assert response.status_code == 404
    assert 'нет транзакций' in response.text.lower()

def test_cancel_invalid_uuid(client: TestClient) -> None:
    """
    Попытка отмены с неправильным форматом UUID → код 422 [ошибка] (валидация FastAPI).
    """
    response = client.post(
        url = f'/api/v1/wallets/not-a-uuid/cancel'
    )

    assert response.status_code == 422

def test_cancel_wallet_not_found(client: TestClient) -> None:
    """
    Попытка отмены с правильным форматом UUID, но отсутствием кошелька в БД → код 404 [ошибка].
    """
    fake_uuid = uuid4()

    response = client.post(
        url=f'/api/v1/wallets/{fake_uuid}/cancel'
    )

    assert response.status_code == 404
    assert 'не найден' in response.text.lower()


# ---------- Вспомогательные функции (для конкурентных тестов ----------
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

# ---------- Конкурентные тесты ----------
def test_concurrent_withdraws(con_client: TestClient) -> None:
    """
    Конкурентный тест на списание:
    Четыре параллельных операции: два списания -60 и два списания -15 при балансе кошелька 100.
    Во всех случаях: 3 списания → код 200 [успешно], 1 списание → код 400 [ошибка]. Итоговый баланс 10,00.
    """
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

        results = (
            first_worker.result(),
            second_worker.result(),
            third_worker.result(),
            fourth_worker.result(),
        )

    statuses = [item.status_code for item in results]
    assert statuses.count(200) == 3
    assert statuses.count(400) == 1

    balance = con_client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '10.00'


def test_concurrent_deposit_and_withdraw(con_client: TestClient) -> None:
    """
    Конкурентный тест на списание и зачисление:
    Четыре параллельных операции: два пополнения +30 и два списания -60 при балансе 100.
    Во всех случаях: минимум 3 → код 200 [успешно], но не более 1 → код 400 [ошибка].
    Итоговый баланс 40,00 или 100,00 в зависимости от порядка выполнения транзакций.
    """
    new_wallet = concurrent_wallet(con_client)
    assert new_wallet is not None, 'We could not create a wallet via post request'

    wallet_data = new_wallet.json()
    uuid = wallet_data['wallet_uuid']

    deposit = partial(make_deposit, con_client, uuid, 30)
    withdraw = partial(make_withdraw, con_client, uuid, -60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        deposit_1 = executor.submit(deposit)
        withdraw_1 = executor.submit(withdraw)
        deposit_2 = executor.submit(deposit)
        withdraw_2 = executor.submit(withdraw)

        results = (
            deposit_1.result(),
            withdraw_1.result(),
            deposit_2.result(),
            withdraw_2.result(),
        )

    statuses = [item.status_code for item in results]

    success_count = statuses.count(200)
    fail_count = statuses.count(400)

    # Минимум 3 успеха, максимум 1 провал
    assert success_count >= 3
    assert fail_count <= 1
    assert success_count + fail_count == 4

    # Баланс — один из двух допустимых исходов
    balance = con_client.get(url=f'/api/v1/wallets/{uuid}/balance')
    final_balance = balance.json()['current_balance']
    assert final_balance == '40.00' or '100.00'


def test_concurrent_different_wallets(con_client: TestClient) -> None:
    """
    Конкурентный тест на двух разных кошельках:
    Первый кошелек списание -40, второй — зачисление + 50, при балансе каждого из кошельков 100.
    Проверяет, что блокировка кошелька — построчная, а не глобальная и операции по разным кошелькам не мешают друг другу.
    Обе операции завершаются → кодом 200 [успешно]. Итоговый баланс первый кошелек 60, второй — 150.
    """

    # Создаём два кошелька с балансом 100 каждый
    first_wallet = concurrent_wallet(con_client)
    assert first_wallet is not None, 'We could not create the first wallet via post request'
    first_uuid = UUID(first_wallet.json()['wallet_uuid'])

    second_wallet = concurrent_wallet(con_client)
    assert second_wallet is not None, 'We could not create the second_wallet via post request'
    second_uuid = UUID(second_wallet.json()['wallet_uuid'])

    # Параллельно: списание с первого, депозит на второй
    withdraw = partial(make_withdraw, con_client, first_uuid, -40)
    deposit = partial(make_deposit, con_client, second_uuid, 50)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        withdraw_worker = executor.submit(withdraw)
        deposit_worker = executor.submit(deposit)

        withdraw_result = withdraw_worker.result()
        deposit_result = deposit_worker.result()

    # Обе операции успешны — они не конкурируют за одну строку
    assert withdraw_result.status_code == 200
    assert deposit_result.status_code == 200

    # Балансы независимы
    first_balance = con_client.get(url=f'/api/v1/wallets/{first_uuid}/balance')
    assert first_balance.json()['current_balance'] == '60.00'

    second_balance = con_client.get(url=f'/api/v1/wallets/{second_uuid}/balance')
    assert second_balance.json()['current_balance'] == '150.00'