"""SQLite storage. Every SQL statement of the project lives in this module.

Queries are always parameterized (`?`); no SQL is ever built from data.
"""

import sqlite3
from pathlib import Path

# Schema version N = the first N scripts applied, tracked in PRAGMA user_version.
MIGRATIONS = [
    """
    CREATE TABLE accounts (
        bank TEXT NOT NULL,
        account_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('card', 'jar', 'file')),
        currency TEXT NOT NULL,
        title TEXT NOT NULL,
        balance INTEGER,
        goal INTEGER,
        PRIMARY KEY (bank, account_id)
    ) STRICT;

    CREATE TABLE transactions (
        bank TEXT NOT NULL,
        txn_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        ts INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        currency TEXT NOT NULL,
        operation_amount INTEGER,
        operation_currency TEXT,
        description TEXT NOT NULL,
        mcc INTEGER,
        bank_category TEXT,
        raw TEXT NOT NULL,
        PRIMARY KEY (bank, txn_id),
        FOREIGN KEY (bank, account_id) REFERENCES accounts (bank, account_id)
    ) STRICT;

    CREATE INDEX transactions_ts ON transactions (ts);

    CREATE TABLE sync_state (
        bank TEXT NOT NULL,
        account_id TEXT NOT NULL,
        last_ts INTEGER NOT NULL,
        PRIMARY KEY (bank, account_id)
    ) STRICT;

    -- No foreign key to transactions: overrides are user data and outlive any re-import.
    CREATE TABLE overrides (
        bank TEXT NOT NULL,
        txn_id TEXT NOT NULL,
        category TEXT,
        note TEXT,
        tags TEXT NOT NULL,
        source TEXT NOT NULL CHECK (source IN ('user', 'llm')),
        updated_at INTEGER NOT NULL,
        PRIMARY KEY (bank, txn_id)
    ) STRICT;
    """,
]

SCHEMA_VERSION = len(MIGRATIONS)


def connect(path: str | Path) -> sqlite3.Connection:
    """Open (or create) the database at `path` and bring its schema up to date."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply pending migrations, each together with its version bump in one transaction."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
        try:
            conn.executescript(f"BEGIN; {script}; PRAGMA user_version = {number}; COMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
