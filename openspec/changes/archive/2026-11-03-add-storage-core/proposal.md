# Proposal

## Why

Every later feature (monobank sync, Privat import, categorization, reports, the dashboard) needs one durable
place to keep accounts and transactions. Building it first, with re-import safety and schema versioning in
from day one, avoids duplicated transactions and painful data migrations later.

## What Changes

- Introduce a local SQLite database that stores bank accounts, transactions, per-account sync progress and
  user overrides (manual category, note, tags).
- Saving the same transaction again (same bank and bank transaction id) updates it instead of creating a duplicate.
- Re-importing bank data never touches user overrides.
- The database schema is versioned and upgraded automatically when the database is opened; a database created
  by a newer version of the tool is refused instead of being damaged.
- Money is stored as integer minor units (kopecks/cents) and time as UTC epoch seconds; non-integer amounts are
  rejected.
- The original bank payload of each transaction is kept unchanged for later re-processing.

## Out of scope

- Fetching data from monobank or parsing Privat24 files (steps 2 and 4).
- Currency conversion to UAH and the exchange-rate cache (step 5; it will add a schema migration).
- Categorization logic and transfer detection (step 6).
- Aggregations and reports (step 7), HTTP API and UI (steps 8+).
- Reading configuration/env variables to locate the database (step 3); this change takes an explicit path.

## Capabilities

### New Capabilities
- `transaction-storage`: durable local storage of accounts, transactions, sync progress and user overrides,
  with idempotent saves and versioned schema upgrades.

### Modified Capabilities
<!-- none: there are no existing specs yet -->

## Impact

- New modules: `fin/models.py`, `fin/db.py`; new tests in `tests/`.
- No new dependencies (Python standard library `sqlite3`, `dataclasses`, `json`).
- Creates the database file only at the path the caller passes; personal data stays outside the repository.
