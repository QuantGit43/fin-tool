# Tasks

Every pair is one TDD cycle: write the test, run `uv run pytest` and see it fail for the expected reason
(red), then write the minimal code and see the full suite pass (green). Tests use a temporary SQLite file.

## 1. Data models (`fin/models.py`, `tests/test_models.py`)

- [ ] 1.1 test (red): fractional amount is rejected - `Transaction(amount=123.45, ...)` raises; verify the test fails because `fin.models` does not exist
- [ ] 1.2 impl (green): `Account`, `Transaction`, `Override` dataclasses with integer validation; verify 1.1 passes
- [ ] 1.3 test (red): boolean is not a number - `amount=True` and `ts=False` raise; verify it fails because bools pass the int check
- [ ] 1.4 impl (green): explicit bool rejection; verify the full suite passes
- [ ] 1.5 test (red): incomplete operation currency is rejected - operation amount without currency and currency without amount both raise
- [ ] 1.6 impl (green): both-or-neither check for operation fields; verify the full suite passes
- [ ] 1.7 test (red): unknown account kind `deposit` is rejected; goal on a `card` is rejected; fractional balance or goal is rejected
- [ ] 1.8 impl (green): `Account` validation of `kind`, `balance`, `goal`; verify the full suite passes

## 2. Schema and migrations (`fin/db.py`, `tests/test_db_migrations.py`)

- [ ] 2.1 test (red): empty database is initialized - after `connect(tmp_path / "fin.db")` the schema version is current and all four tables are empty; verify it fails because `fin.db` does not exist
- [ ] 2.2 impl (green): `connect`, `migrate`, migration v1; verify 2.1 passes
- [ ] 2.3 test (red): opening twice is harmless - data and version unchanged after a second `connect`; verify the failure is a real assertion, or record that it passes immediately and why (then strengthen it)
- [ ] 2.4 impl (green): make `migrate` skip applied migrations; verify the full suite passes
- [ ] 2.5 test (red): newer database is refused - set `user_version` above the supported one; `connect` raises an error naming both versions and the file bytes are unchanged
- [ ] 2.6 impl (green): `SchemaVersionError` check before any write; verify the full suite passes

## 3. Accounts and transactions (`fin/db.py`, `tests/test_db_transactions.py`)

- [ ] 3.1 test (red): saving an account twice keeps one account with the new title
- [ ] 3.2 impl (green): `upsert_accounts`, `load_accounts`; verify the full suite passes
- [ ] 3.2a test (red): all accounts listed in order; USD jar keeps kind, currency, balance 35000 and goal 100000; balance refreshed from 1000 to 2500
- [ ] 3.2b impl (green): store and load `kind`, `balance`, `goal`; verify the full suite passes
- [ ] 3.3 test (red): exact round trip - amount -12345 and ts 1767225600 read back unchanged
- [ ] 3.4 impl (green): `upsert_transactions`, `load_transactions`; verify the full suite passes
- [ ] 3.5 test (red): re-importing the same transaction stores one row; bank changed a transaction updates amount and description; same id in different banks stores both
- [ ] 3.6 impl (green): `ON CONFLICT(bank, txn_id) DO UPDATE`; verify the full suite passes
- [ ] 3.7 test (red): unknown account - a batch with one transaction for an unsaved account fails and stores nothing
- [ ] 3.8 impl (green): foreign keys on + one database transaction per batch; verify the full suite passes
- [ ] 3.9 test (red): half-open range - rows at start and inside returned in order, row at end excluded; nothing in range returns empty
- [ ] 3.10 impl (green): range query with ordering; verify the full suite passes
- [ ] 3.11 test (red): payload round trip with non-ASCII, quotes and nesting; description `'); DROP TABLE transactions; --` stored literally and data intact
- [ ] 3.12 impl (green): only if 3.11 fails - otherwise record that parameterized queries already satisfy it; verify the full suite passes
- [ ] 3.13 test (red): purchase in a foreign currency keeps -84250 UAH and -2000 EUR; operation in the account currency reads back with empty operation fields
- [ ] 3.14 impl (green): store and load `operation_amount`/`operation_currency`; verify the full suite passes

## 4. Sync progress and overrides (`fin/db.py`, `tests/test_db_state.py`)

- [ ] 4.1 test (red): never synced returns None; progress is updated to the later timestamp
- [ ] 4.2 impl (green): `get_sync_state`, `set_sync_state`; verify the full suite passes
- [ ] 4.3 test (red): override round trip keeps category, note and tag order; no override returns None
- [ ] 4.4 impl (green): `get_override`, `set_override`; verify the full suite passes
- [ ] 4.5 test (red): override kept after the same transaction is re-imported
- [ ] 4.6 impl (green): only if 4.5 fails; verify the full suite passes

## 5. Clean-up and checks

- [ ] 5.1 refactor: remove duplication in tests (shared fixtures in `tests/conftest.py`), keep the suite green
- [ ] 5.2 run `uv run pytest`, `pre-commit run --all-files` and `openspec validate add-storage-core --strict`; all pass

## Workflow follow-up

- Gate B: show red/green evidence and the diff; wait for the user's approval.
- `openspec archive add-storage-core`, push the branch, open the PR, wait for green CI and the user's approval, then merge.
