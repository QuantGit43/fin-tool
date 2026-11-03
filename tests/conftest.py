import pytest

from fin import db
from tests.factories import make_account


@pytest.fixture
def conn(tmp_path):
    """A real SQLite database in a temporary file, deleted after the test."""
    connection = db.connect(tmp_path / "fin.db")
    yield connection
    connection.close()


@pytest.fixture
def account(conn):
    """The default account from make_account(), already saved."""
    db.upsert_accounts(conn, [make_account()])
