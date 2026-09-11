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


def test_get_balance(client: TestClient, wallet: Wallet | None, db_session: Session) -> None:
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
def override_get_db_factory() -> Generator[Session, Any, None]:
    """
    Каждому запросу — своя сессия, как в проде.
    """
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

app.dependency_overrides[get_db] = override_get_db

with TestClient(app) as test_client:
    yield test_client

app.dependency_overrides.pop(get_db, None)










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


def _run_in_own_session(func, wallet_uuid, amount):
    """
    Запускает сервисную функцию в отдельной сессии.
    Возвращает (status, result_or_error).
    """
    session: Session = TestingSession()
    try:
        result = func(session, wallet_uuid, amount)
        return ('ok', result)
    except Exception as exc:
        return ('err', exc)
    finally:
        session.close()

# ----------- Конкурентные тесты -----------
def test_concurrent_withdrawals(client: TestClient, wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    # Фиксируем client и uuid, оставляем только amount
    withdraw = partial(make_withdraw, client, uuid, -60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        first_worker = executor.submit(withdraw)
        second_worker = executor.submit(withdraw)

        first_result, second_result = first_worker.result(), second_worker.result()

    response = {first_result.status_code, second_result.status_code}
    assert response == {200, 400}  # один успех, одна ошибка

    balance = client.get(url=f'/api/v1/wallets/{uuid}/balance')
    assert balance.json()['current_balance'] == '40.00'


def _run_in_own_session(func, wallet_uuid, amount):
    """
    Запускает сервисную функцию в отдельной сессии.
    Возвращает (status, result_or_error).
    """
    session: Session = TestingSession()
    try:
        result = func(session, wallet_uuid, amount)
        return ('ok', result)
    except Exception as exc:
        return ('err', exc)
    finally:
        session.close()


def test_concurrent_deposit_and_withdraw(wallet: Wallet | None) -> None:
    assert wallet is not None, 'Wallet fixture did not create a wallet'
    uuid = wallet.uuid

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        deposit_future = executor.submit(
            _run_in_own_session, make_deposit, uuid, Decimal('30')
        )
        withdraw_future = executor.submit(
            _run_in_own_session, make_withdraw, uuid, Decimal('-40')
        )

        deposit_status, deposit_result = deposit_future.result()
        withdraw_status, withdraw_result = withdraw_future.result()

    # Обе операции должны завершиться успешно
    assert deposit_status == 'ok', f'deposit failed: {deposit_result!r}'
    assert withdraw_status == 'ok', f'withdraw failed: {withdraw_result!r}'

    # Проверяем итоговый баланс отдельной сессией
    check_session: Session = TestingSession()
    try:
        check_session.expire_all()
        wallet_after = (
            check_session.query(Wallet).filter(Wallet.uuid == uuid).one()
        )
        assert wallet_after.balance == Decimal('90.00'), (
            f'expected 90.00, got {wallet_after.balance}'
        )
    finally:
        check_session.close()