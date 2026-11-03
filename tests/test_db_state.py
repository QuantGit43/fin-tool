import pytest

from fin import db


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
