import pytest

from fin import db
from fin.models import Account, Override, Transaction


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "fin.db")
    yield connection
    connection.close()


def test_never_synced(conn):
    assert db.get_sync_state(conn, "mono", "acc-1") is None


def test_progress_is_updated(conn):
    db.set_sync_state(conn, "mono", "acc-1", 1767225600)
    db.set_sync_state(conn, "mono", "acc-1", 1769904000)

    assert db.get_sync_state(conn, "mono", "acc-1") == 1769904000
    assert db.get_sync_state(conn, "mono", "other") is None


def test_override_round_trip(conn):
    override = Override(
        bank="mono",
        txn_id="t-1",
        updated_at=1767225600,
        category="Restaurants",
        note="Dinner with friends",
        tags=("trip", "family"),
    )
    db.set_override(conn, override)

    assert db.get_override(conn, "mono", "t-1") == override


def test_no_override(conn):
    assert db.get_override(conn, "mono", "t-1") is None


def test_override_kept_after_reimport(conn):
    account = Account(bank="mono", account_id="acc-1", kind="card", currency="UAH", title="Black card")
    txn = Transaction(
        bank="mono", account_id="acc-1", txn_id="t-1", ts=1767225600, amount=-12345,
        currency="UAH", description="Grocery store", raw="{}",
    )
    override = Override(bank="mono", txn_id="t-1", updated_at=1767225600, category="Groceries")
    db.upsert_accounts(conn, [account])
    db.upsert_transactions(conn, [txn])
    db.set_override(conn, override)

    db.upsert_transactions(conn, [txn])

    assert db.get_override(conn, "mono", "t-1") == override
