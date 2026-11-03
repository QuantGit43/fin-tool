# Design

## Context

The repository has only the scaffold (`fin/__init__.py`, one smoke test). This change adds the first real
modules. Motivation and scope: see proposal.md. Behavior: see specs/transaction-storage/spec.md.

## Goals / Non-Goals

**Goals:**
- One module (`fin/db.py`) owns every SQL statement, so swapping the database later touches only this file.
- Plain data objects (`fin/models.py`) shared by sources, storage and reports.
- Tests run on a real SQLite database (temporary file), no mocks.

**Non-Goals:**
- Connection pooling, concurrency control, async access - one local user, one process at a time.
- Query filters beyond the time range (bank/account/category filters arrive with reports in step 7).
- Locating the database from env/config (step 3).

## Decisions

### Standard-library `sqlite3`, no ORM
Five small tables and simple queries do not justify SQLAlchemy plus Alembic (decided with the user during
planning). Alternative considered: SQLAlchemy Core - kept as the upgrade path if the database changes.

### Public interface of `fin/db.py`
- `connect(path) -> sqlite3.Connection` - opens the file (or `":memory:"`), enables foreign keys, runs `migrate`.
- `migrate(conn)` - applies pending migrations; refuses newer schemas.
- `upsert_accounts(conn, accounts)`, `upsert_transactions(conn, transactions)` - one transaction per call
  (`with conn:`), so a failing batch rolls back completely.
- `load_transactions(conn, start_ts, end_ts) -> list[Transaction]` - half-open `[start, end)`.
- `get_sync_state(conn, bank, account_id) -> int | None`, `set_sync_state(conn, bank, account_id, last_ts)`.
- `get_override(conn, bank, txn_id) -> Override | None`, `set_override(conn, override)`.

`load_transactions` returns dataclasses, not a pandas DataFrame (planning said DataFrame): it keeps
`db.py` free of pandas until reports need it, and `reports.py` can build a DataFrame from the list in one
line. The "swap the database by rewriting only db.py" property is unchanged.

### Migrations: ordered list + `PRAGMA user_version`
`MIGRATIONS = [sql_v1, ...]`; version N = first N scripts applied. `migrate` reads `user_version`; if it is
greater than `len(MIGRATIONS)` it raises `SchemaVersionError` before writing anything; otherwise each pending
script and the new `user_version` are applied inside one transaction, so a failed upgrade leaves the old
version intact. Alternative considered: a `schema_version` table - equivalent, but `user_version` needs no
extra table; it stays isolated inside `migrate()` so a Postgres port can switch to a table.

### Schema v1
- `accounts(bank TEXT, account_id TEXT, type TEXT, currency TEXT, title TEXT, PRIMARY KEY(bank, account_id))`
- `transactions(bank TEXT, txn_id TEXT, account_id TEXT, ts INTEGER, amount INTEGER, currency TEXT,
  operation_amount INTEGER NULL, operation_currency TEXT NULL,
  description TEXT, mcc INTEGER NULL, bank_category TEXT NULL, raw TEXT,
  PRIMARY KEY(bank, txn_id), FOREIGN KEY(bank, account_id) REFERENCES accounts)`, index on `ts`.
- `sync_state(bank TEXT, account_id TEXT, last_ts INTEGER, PRIMARY KEY(bank, account_id))`
- `overrides(bank TEXT, txn_id TEXT, category TEXT NULL, note TEXT NULL, tags TEXT /* JSON array */,
  source TEXT CHECK(source IN ('user','llm')), updated_at INTEGER, PRIMARY KEY(bank, txn_id))`
  - No foreign key to `transactions`: an override must survive even if a bank transaction is re-imported,
    and the table is never written by bank upserts.
- `amount` is in the account currency; `operation_amount`/`operation_currency` hold the original operation
  (monobank `operationAmount`/`currencyCode`) when it differs, for display and trip analysis. Budgets and
  reports never use them directly. Converted UAH amounts and the rates cache come in step 5 as
  migration v2 (`amount_uah` column + `rates` table).
- Currency is ISO 4217 alphabetic code (`"UAH"`); sources convert monobank's numeric codes.
- Amounts are in the currency's ISO 4217 minor units (2 decimals for UAH/USD/EUR, 0 for JPY); storage does
  not interpret them. Formatting by currency exponent belongs to step 5/8.

### Idempotent upsert
`INSERT ... ON CONFLICT(bank, txn_id) DO UPDATE SET <all bank fields> = excluded.<field>` - the same syntax
works on PostgreSQL. All values go through `?` placeholders; no SQL is ever built from data.

### Validation in the dataclasses
`Transaction.__post_init__` rejects `amount`/`ts` that are not `int` or are `bool` (`isinstance(True, int)`
is true in Python, hence the explicit check), `mcc`/`operation_amount` that are neither `None` nor such an
int, and an `operation_amount` without `operation_currency` (or vice versa). This is the
trust boundary every source passes through, so a float can never reach the database.

### Overrides
`Override(bank, txn_id, category=None, note=None, tags=(), source="user", updated_at=int)`; tags stored as a
JSON array to keep their order. `updated_at` is passed in by the caller (no hidden clock), which keeps tests
deterministic.

## Risks / Trade-offs

- [`PRAGMA foreign_keys` is off by default in SQLite] → `connect()` always enables it; a test covers the
  unknown-account rejection.
- [`user_version` is SQLite-specific] → isolated in `migrate()`; documented upgrade path to a version table.
- [`raw` can be large] → statements are small (thousands per year); no compression needed.
- [Bank updates overwrite earlier values silently] → intended (holds become final); the original payload of
  the latest import is kept in `raw`.
