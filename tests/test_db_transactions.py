import sqlite3

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


def test_reimporting_the_same_transaction(conn, account):
    db.upsert_transactions(conn, [make_txn()])
    db.upsert_transactions(conn, [make_txn()])

    assert everything(conn) == [make_txn()]


def test_bank_changed_a_transaction(conn, account):
    db.upsert_transactions(conn, [make_txn(amount=-100, description="Pending")])
    db.upsert_transactions(conn, [make_txn(amount=-150, description="Final")])

    assert everything(conn) == [make_txn(amount=-150, description="Final")]


def test_same_id_in_different_banks(conn, account):
    db.upsert_accounts(conn, [make_account(bank="privat", kind="file")])
    mono = make_txn(bank="mono")
    privat = make_txn(bank="privat")
    db.upsert_transactions(conn, [mono, privat])

    assert sorted(everything(conn), key=lambda t: t.bank) == [mono, privat]


def test_unknown_account_rejects_the_whole_batch(conn, account):
    good = make_txn(txn_id="t-good")
    orphan = make_txn(txn_id="t-orphan", account_id="never-saved")

    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_transactions(conn, [good, orphan])

    assert everything(conn) == []


def test_half_open_range(conn, account):
    start, end = 1767225600, 1769904000  # 2026-01-01 and 2026-02-01, 00:00 UTC
    at_start = make_txn(txn_id="t-start", ts=start)
    inside_b = make_txn(txn_id="t-b", ts=start + 3600)
    inside_a = make_txn(txn_id="t-a", ts=start + 3600)
    at_end = make_txn(txn_id="t-end", ts=end)
    before = make_txn(txn_id="t-before", ts=start - 1)
    db.upsert_transactions(conn, [at_end, inside_b, before, inside_a, at_start])

    assert db.load_transactions(conn, start, end) == [at_start, inside_a, inside_b]


def test_nothing_in_range(conn, account):
    db.upsert_transactions(conn, [make_txn(ts=1767225600)])

    assert db.load_transactions(conn, 1800000000, 1800086400) == []


def test_payload_round_trip(conn, account):
    payload = '{"description": "Сільпо \\"Кур\'єр\\"", "nested": {"tags": ["a", "б"], "n": 1.5}}'
    db.upsert_transactions(conn, [make_txn(raw=payload)])

    assert everything(conn)[0].raw == payload


def test_description_that_looks_like_a_database_command(conn, account):
    hostile = "'); DROP TABLE transactions; --"
    db.upsert_transactions(conn, [make_txn(txn_id="t-1"), make_txn(txn_id="t-2", description=hostile)])

    stored = everything(conn)
    assert [t.description for t in stored] == ["Grocery store", hostile]
    assert db.load_accounts(conn) == [make_account()]


def test_purchase_in_a_foreign_currency(conn, account):
    txn = make_txn(amount=-84250, currency="UAH", operation_amount=-2000, operation_currency="EUR")
    db.upsert_transactions(conn, [txn])

    [stored] = everything(conn)
    assert (stored.amount, stored.currency) == (-84250, "UAH")
    assert (stored.operation_amount, stored.operation_currency) == (-2000, "EUR")


def test_operation_in_the_account_currency(conn, account):
    db.upsert_transactions(conn, [make_txn()])

    [stored] = everything(conn)
    assert (stored.operation_amount, stored.operation_currency) == (None, None)
