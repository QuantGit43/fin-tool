# Tasks

Every pair is one TDD cycle: write the test, run `uv run pytest` and see it fail for the expected reason
(red), then write the minimal code and see the full suite pass (green). Tests use a temporary SQLite file.

## 1. Data models (`fin/models.py`, `tests/test_models.py`)

- [x] 1.1 test (red): fractional amount is rejected - `Transaction(amount=123.45, ...)` raises; verify the test fails because `fin.models` does not exist
- [x] 1.2 impl (green): `Account`, `Transaction`, `Override` dataclasses with integer validation; verify 1.1 passes
- [x] 1.3 test (red): boolean is not a number - `amount=True` and `ts=False` raise; verify it fails because bools pass the int check
- [x] 1.4 impl (green): explicit bool rejection; verify the full suite passes
- [x] 1.5 test (red): incomplete operation currency is rejected - operation amount without currency and currency without amount both raise
- [x] 1.6 impl (green): both-or-neither check for operation fields; verify the full suite passes
- [x] 1.7 test (red): unknown account kind `deposit` is rejected; goal on a `card` is rejected; fractional balance or goal is rejected
- [x] 1.8 impl (green): `Account` validation of `kind`, `balance`, `goal`; verify the full suite passes

## 2. Schema and migrations (`fin/db.py`, `tests/test_db_migrations.py`)

- [x] 2.1 test (red): empty database is initialized - after `connect(tmp_path / "fin.db")` the schema version is current and all four tables are empty; verify it fails because `fin.db` does not exist
- [x] 2.2 impl (green): `connect`, `migrate`, migration v1; verify 2.1 passes
- [x] 2.3 test (red): opening twice is harmless - data and version unchanged after a second `connect`; verify the failure is a real assertion, or record that it passes immediately and why (then strengthen it)
- [x] 2.4 impl (green): make `migrate` skip applied migrations; verify the full suite passes (no code needed: 2.2 already skips applied scripts; 2.3 test proven by mutation - re-running all migrations fails it)
- [x] 2.5 test (red): newer database is refused - set `user_version` above the supported one; `connect` raises an error naming both versions and the file bytes are unchanged
- [x] 2.6 impl (green): `SchemaVersionError` check before any write; verify the full suite passes

## 3. Accounts and transactions (`fin/db.py`, `tests/test_db_transactions.py`)

- [x] 3.1 test (red): saving an account twice keeps one account with the new title
- [x] 3.2 impl (green): `upsert_accounts`, `load_accounts`; verify the full suite passes
- [x] 3.2a test (red): all accounts listed in order; USD jar keeps kind, currency, balance 35000 and goal 100000; balance refreshed from 1000 to 2500
- [x] 3.2b impl (green): store and load `kind`, `balance`, `goal`; verify the full suite passes (already done in 3.2; 3.2a tests proven by mutation - balance not updated)
- [x] 3.3 test (red): exact round trip - amount -12345 and ts 1767225600 read back unchanged
- [x] 3.4 impl (green): `upsert_transactions`, `load_transactions`; verify the full suite passes
- [x] 3.5 test (red): re-importing the same transaction stores one row; bank changed a transaction updates amount and description; same id in different banks stores both
- [x] 3.6 impl (green): `ON CONFLICT(bank, txn_id) DO UPDATE`; verify the full suite passes
- [x] 3.7 test (red): unknown account - a batch with one transaction for an unsaved account fails and stores nothing
- [x] 3.8 impl (green): foreign keys on + one database transaction per batch; verify the full suite passes (already in `connect` and `with conn`; 3.7 test proven by mutation - foreign keys off)
- [x] 3.9 test (red): half-open range - rows at start and inside returned in order, row at end excluded; nothing in range returns empty
- [x] 3.10 impl (green): range query with ordering; verify the full suite passes
- [x] 3.11 test (red): payload round trip with non-ASCII, quotes and nesting; description `'); DROP TABLE transactions; --` stored literally and data intact
- [x] 3.12 impl (green): only if 3.11 fails - otherwise record that parameterized queries already satisfy it; verify the full suite passes (parameterized queries already satisfy it; proven by mutation - f-string SQL breaks on the hostile description)
- [x] 3.13 test (red): purchase in a foreign currency keeps -84250 UAH and -2000 EUR; operation in the account currency reads back with empty operation fields
- [x] 3.14 impl (green): store and load `operation_amount`/`operation_currency`; verify the full suite passes (columns stored since 3.4; proven by mutation - columns dropped)

## 4. Sync progress and overrides (`fin/db.py`, `tests/test_db_state.py`)

- [x] 4.1 test (red): never synced returns None; progress is updated to the later timestamp
- [x] 4.2 impl (green): `get_sync_state`, `set_sync_state`; verify the full suite passes
- [x] 4.3 test (red): override round trip keeps category, note and tag order; no override returns None
- [x] 4.4 impl (green): `get_override`, `set_override`; verify the full suite passes
- [x] 4.5 test (red): override kept after the same transaction is re-imported
- [x] 4.6 impl (green): only if 4.5 fails; verify the full suite passes (not needed: bank upserts never touch overrides; proven by mutation - upsert deleting overrides fails 4.5)

## 5. Clean-up and checks

- [x] 5.1 refactor: remove duplication in tests (shared fixtures in `tests/conftest.py`), keep the suite green
- [x] 5.2 run `uv run pytest`, `pre-commit run --all-files` and `openspec validate add-storage-core --strict`; all pass

## Workflow follow-up

- Gate B: show red/green evidence and the diff; wait for the user's approval.
- `openspec archive add-storage-core`, push the branch, open the PR, wait for green CI and the user's approval, then merge.
