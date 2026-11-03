"""SQLite storage. Every SQL statement of the project lives in this module.

Queries are always parameterized (`?`); no SQL is ever built from data.
"""

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from fin.models import Account, Transaction

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


class SchemaVersionError(RuntimeError):
    """The database was created by a newer version of fin-tool."""


def connect(path: str | Path) -> sqlite3.Connection:
    """Open (or create) the database at `path` and bring its schema up to date."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        migrate(conn)
    except Exception:
        conn.close()
        raise
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply pending migrations, each together with its version bump in one transaction."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise SchemaVersionError(
            f"database schema version {version} is newer than supported version {SCHEMA_VERSION}; "
            "update fin-tool instead of opening this database with an older version"
        )
    for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
        try:
            conn.executescript(f"BEGIN; {script}; PRAGMA user_version = {number}; COMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise


_ACCOUNT_COLUMNS = ("bank", "account_id", "kind", "currency", "title", "balance", "goal")


def upsert_accounts(conn: sqlite3.Connection, accounts: Iterable[Account]) -> None:
    """Insert accounts or update the existing ones (same bank and account id)."""
    with conn:
        conn.executemany(
            """
            INSERT INTO accounts (bank, account_id, kind, currency, title, balance, goal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (bank, account_id) DO UPDATE SET
                kind = excluded.kind,
                currency = excluded.currency,
                title = excluded.title,
                balance = excluded.balance,
                goal = excluded.goal
            """,
            [tuple(getattr(a, c) for c in _ACCOUNT_COLUMNS) for a in accounts],
        )


def load_accounts(conn: sqlite3.Connection) -> list[Account]:
    rows = conn.execute(
        "SELECT bank, account_id, kind, currency, title, balance, goal FROM accounts "
        "ORDER BY bank, account_id"
    )
    return [Account(*row) for row in rows]


# Same order as the Transaction dataclass fields.
_TRANSACTION_COLUMNS = (
    "bank", "account_id", "txn_id", "ts", "amount", "currency", "description", "raw",
    "mcc", "bank_category", "operation_amount", "operation_currency",
)


_KEY_COLUMNS = ("bank", "txn_id")

# Built once from the constant column names above, never from data.
_UPSERT_TRANSACTION = (
    f"INSERT INTO transactions ({', '.join(_TRANSACTION_COLUMNS)}) "
    f"VALUES ({', '.join('?' * len(_TRANSACTION_COLUMNS))}) "
    f"ON CONFLICT ({', '.join(_KEY_COLUMNS)}) DO UPDATE SET "
    + ", ".join(f"{c} = excluded.{c}" for c in _TRANSACTION_COLUMNS if c not in _KEY_COLUMNS)
)


def upsert_transactions(conn: sqlite3.Connection, transactions: Iterable[Transaction]) -> None:
    """Insert transactions or replace the bank fields of existing ones (same bank and txn id)."""
    with conn:
        conn.executemany(
            _UPSERT_TRANSACTION,
            [tuple(getattr(t, c) for c in _TRANSACTION_COLUMNS) for t in transactions],
        )


def load_transactions(conn: sqlite3.Connection, start_ts: int, end_ts: int) -> list[Transaction]:
    rows = conn.execute(f"SELECT {', '.join(_TRANSACTION_COLUMNS)} FROM transactions")
    return [Transaction(*row) for row in rows]
