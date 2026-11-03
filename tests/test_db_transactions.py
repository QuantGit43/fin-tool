import pytest

from fin import db
from fin.models import Account


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "fin.db")
    yield connection
    connection.close()


def make_account(**changes):
    fields = dict(bank="mono", account_id="acc-1", kind="card", currency="UAH", title="Black card")
    fields.update(changes)
    return Account(**fields)


def test_saving_an_account_twice_keeps_one(conn):
    db.upsert_accounts(conn, [make_account(title="Old title")])
    db.upsert_accounts(conn, [make_account(title="New title")])

    assert db.load_accounts(conn) == [make_account(title="New title")]
