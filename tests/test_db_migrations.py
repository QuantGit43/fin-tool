import sqlite3

import pytest

from fin import db

TABLES = ("accounts", "transactions", "sync_state", "overrides")


def test_empty_database_is_initialized(tmp_path):
    conn = db.connect(tmp_path / "fin.db")

    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    for table in TABLES:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_opening_twice_is_harmless(tmp_path):
    path = tmp_path / "fin.db"
    conn = db.connect(path)
    with conn:
        conn.execute("INSERT INTO sync_state VALUES ('mono', 'acc-1', 1767225600)")
    conn.close()

    conn = db.connect(path)

    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    assert conn.execute("SELECT * FROM sync_state").fetchall() == [("mono", "acc-1", 1767225600)]


def test_newer_database_is_refused(tmp_path):
    path = tmp_path / "fin.db"
    future = db.SCHEMA_VERSION + 1
    raw = sqlite3.connect(path)
    raw.execute(f"PRAGMA user_version = {future}")
    raw.close()
    before = path.read_bytes()

    with pytest.raises(db.SchemaVersionError) as error:
        db.connect(path)

    assert str(future) in str(error.value)
    assert str(db.SCHEMA_VERSION) in str(error.value)
    assert path.read_bytes() == before
