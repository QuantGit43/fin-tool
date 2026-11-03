from fin import db

TABLES = ("accounts", "transactions", "sync_state", "overrides")


def test_empty_database_is_initialized(tmp_path):
    conn = db.connect(tmp_path / "fin.db")

    assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
    for table in TABLES:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
