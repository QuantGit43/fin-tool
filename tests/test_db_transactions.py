import pytest

from fin import db
from fin.models import Account, Transaction


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "fin.db")
    yield connection
    connection.close()


def make_account(**changes):
    fields = dict(bank="mono", account_id="acc-1", kind="card", currency="UAH", title="Black card")
    fields.update(changes)
    return Account(**fields)


def make_txn(**changes):
    fields = dict(
        bank="mono",
        account_id="acc-1",
        txn_id="t-1",
        ts=1767225600,
        amount=-12345,
        currency="UAH",
        description="Grocery store",
        raw='{"id": "t-1"}',
    )
    fields.update(changes)
    return Transaction(**fields)


def everything(conn):
    return db.load_transactions(conn, 0, 2**62)


@pytest.fixture
def account(conn):
    db.upsert_accounts(conn, [make_account()])


def test_saving_an_account_twice_keeps_one(conn):
    db.upsert_accounts(conn, [make_account(title="Old title")])
    db.upsert_accounts(conn, [make_account(title="New title")])

    assert db.load_accounts(conn) == [make_account(title="New title")]


def test_all_accounts_are_listed_in_order(conn):
    jar = make_account(account_id="jar-1", kind="jar", title="Trip")
    card = make_account(account_id="acc-1")
    privat = make_account(bank="privat", account_id="acc-0", kind="file")
    db.upsert_accounts(conn, [jar, privat, card])

    assert db.load_accounts(conn) == [card, jar, privat]


def test_jar_in_a_foreign_currency(conn):
    jar = make_account(account_id="jar-usd", kind="jar", currency="USD", balance=35000, goal=100000)
    db.upsert_accounts(conn, [jar])

    [stored] = db.load_accounts(conn)
    assert (stored.kind, stored.currency, stored.balance, stored.goal) == ("jar", "USD", 35000, 100000)


def test_balance_is_refreshed(conn):
    db.upsert_accounts(conn, [make_account(balance=1000)])
    db.upsert_accounts(conn, [make_account(balance=2500)])

    assert db.load_accounts(conn)[0].balance == 2500


def test_exact_round_trip(conn, account):
    txn = make_txn(amount=-12345, ts=1767225600)
    db.upsert_transactions(conn, [txn])

    assert everything(conn) == [txn]
