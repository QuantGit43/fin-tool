import pytest

from fin import db
from fin.models import Override


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
