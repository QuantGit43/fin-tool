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
