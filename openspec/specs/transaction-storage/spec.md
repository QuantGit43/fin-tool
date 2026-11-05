# transaction-storage Specification

## Purpose
Keeps the user's bank accounts, transactions, sync progress and manual overrides in one local database,
so that repeated imports are safe and later features can read consistent data.

## Requirements

### Requirement: Database schema is created and upgraded on open
The system SHALL create all storage tables when it opens an empty database, and SHALL apply any pending
schema upgrades in order when it opens a database created by an older version. Opening an up-to-date
database SHALL change nothing.

#### Scenario: Empty database is initialized
- **WHEN** the storage is opened on a path where no database exists
- **THEN** a database is created with the current schema version and empty accounts, transactions, sync progress and overrides

#### Scenario: Opening twice is harmless
- **WHEN** the storage is opened again on a database that already has the current schema version and stored data
- **THEN** the schema version and all stored data are unchanged

### Requirement: Newer databases are refused
The system SHALL refuse to open a database whose schema version is newer than the version it supports,
and SHALL leave that database unchanged.

#### Scenario: Database from a newer tool version
- **WHEN** the storage is opened on a database whose schema version is higher than the supported one
- **THEN** opening fails with an error that names both versions and the database file is not modified

### Requirement: Accounts are saved idempotently
The system SHALL store an account identified by bank and account id, and saving an account that already
exists SHALL update its type, currency and title instead of creating a second account.

#### Scenario: Saving an account twice
- **WHEN** an account is saved and then saved again with the same bank and account id but a new title
- **THEN** exactly one account exists for that bank and account id and it has the new title

#### Scenario: All accounts are listed
- **WHEN** a card and a jar are saved and the accounts are read
- **THEN** both are returned, ordered by bank and account id

### Requirement: Accounts have a kind
The system SHALL store each account's kind as one of `card` (a bank card or current account), `jar`
(a monobank savings jar) or `file` (an account known only from an imported statement file), and SHALL
reject any other kind.

#### Scenario: Unknown kind is rejected
- **WHEN** an account is created with the kind `deposit`
- **THEN** it is rejected with an error before anything is stored

### Requirement: Account balance and jar goal are kept
The system SHALL store, for each account, its optional current balance in minor units of the account
currency as of the last save, and, for jars, an optional savings goal in the same units. Saving the
account again SHALL replace both values.

#### Scenario: Jar in a foreign currency
- **WHEN** a jar with currency USD, balance 35000 cents and goal 100000 cents is saved and read back
- **THEN** it has kind `jar`, currency USD, balance 35000 and goal 100000

#### Scenario: Balance is refreshed
- **WHEN** an account is saved with balance 1000 and then saved again with balance 2500
- **THEN** reading it returns balance 2500

#### Scenario: Goal only for jars
- **WHEN** an account of kind `card` is created with a goal
- **THEN** it is rejected with an error before anything is stored

#### Scenario: Fractional balance is rejected
- **WHEN** an account is created with a balance or goal that is not a whole number
- **THEN** it is rejected with an error before anything is stored

### Requirement: Transactions are saved idempotently
The system SHALL identify a transaction by bank and bank transaction id. Saving a transaction that already
exists SHALL replace its bank-provided fields with the new values and SHALL NOT create a duplicate.

#### Scenario: Re-importing the same transaction
- **WHEN** the same transaction is saved twice
- **THEN** exactly one transaction with that bank and transaction id is stored

#### Scenario: Bank changed a transaction
- **WHEN** a transaction is saved again with the same bank and transaction id but a different amount or description
- **THEN** the stored transaction has the new amount and description

#### Scenario: Same id in different banks
- **WHEN** two transactions with the same transaction id but different banks are saved
- **THEN** both transactions are stored

### Requirement: Transactions belong to a known account
The system SHALL reject a transaction whose bank and account id do not match a stored account, and SHALL
store none of the transactions passed in that same save.

#### Scenario: Unknown account
- **WHEN** a batch of transactions is saved and one of them references an account that was never saved
- **THEN** the save fails and none of the transactions from that batch are stored

### Requirement: Money and time use exact integer units
The system SHALL accept transaction amounts only as whole numbers of minor currency units (kopecks, cents)
and timestamps only as whole UTC epoch seconds, and SHALL return them unchanged.

#### Scenario: Exact round trip
- **WHEN** a transaction with amount -12345 kopecks and timestamp 1767225600 is saved and read back
- **THEN** the read transaction has amount -12345 and timestamp 1767225600

#### Scenario: Fractional amount is rejected
- **WHEN** a transaction is created with an amount that is not a whole number, such as 123.45
- **THEN** it is rejected with an error before anything is stored

#### Scenario: Boolean is not a number
- **WHEN** a transaction is created with an amount or timestamp given as true or false
- **THEN** it is rejected with an error before anything is stored

### Requirement: Operation currency is kept alongside account currency
The system SHALL store, in addition to the amount in the account currency, the optional amount and currency
of the operation itself (for example a purchase in EUR paid from a UAH account). Operation amount and
operation currency SHALL be given together or not at all, and the operation amount SHALL be a whole number
of minor units.

#### Scenario: Purchase in a foreign currency
- **WHEN** a transaction of -84250 UAH kopecks for an operation of -2000 EUR cents is saved and read back
- **THEN** it has amount -84250 in UAH and operation amount -2000 in EUR

#### Scenario: Operation in the account currency
- **WHEN** a transaction without operation amount and operation currency is saved and read back
- **THEN** both operation fields are empty

#### Scenario: Incomplete operation currency is rejected
- **WHEN** a transaction is created with an operation amount but no operation currency, or the other way round
- **THEN** it is rejected with an error before anything is stored

### Requirement: Original bank payload is preserved
The system SHALL store the original bank payload of each transaction as text and SHALL return it exactly
as it was saved.

#### Scenario: Payload round trip
- **WHEN** a transaction is saved with a payload containing non-ASCII text, quotes and nested values
- **THEN** reading it back returns a payload identical to the saved one

### Requirement: Transactions are read by time range
The system SHALL return the transactions whose timestamp is at or after the range start and strictly before
the range end, ordered by timestamp and then by bank and transaction id.

#### Scenario: Half-open range
- **WHEN** transactions exist at the range start, inside the range and exactly at the range end, and the range is read
- **THEN** the transactions at the start and inside are returned in time order and the one at the end is not

#### Scenario: Nothing in range
- **WHEN** a range with no transactions is read
- **THEN** an empty result is returned

### Requirement: Untrusted text is stored literally
The system SHALL store transaction descriptions and other bank-provided text exactly as given, without
interpreting them, including text that looks like database commands or markup.

#### Scenario: Description that looks like a database command
- **WHEN** a transaction with the description `'); DROP TABLE transactions; --` is saved and read back
- **THEN** the description is returned unchanged and all stored data is still present

### Requirement: Sync progress is tracked per account
The system SHALL store, per bank and account, the timestamp up to which data has been synced, return none
for an account that was never synced, and overwrite the value when it is saved again.

#### Scenario: Never synced
- **WHEN** sync progress is read for an account that has never been synced
- **THEN** no timestamp is returned

#### Scenario: Progress is updated
- **WHEN** sync progress is saved for an account and then saved again with a later timestamp
- **THEN** reading it returns the later timestamp

### Requirement: User overrides survive re-imports
The system SHALL store user overrides (category, note, tags, and whether a user or an automated categorizer
set them) separately from bank data, keyed by bank and transaction id, and saving bank transactions SHALL
never change or remove them.

#### Scenario: Override kept after re-import
- **WHEN** a user override is set for a transaction and the same transaction is then saved again from the bank
- **THEN** the override is unchanged

#### Scenario: Override round trip
- **WHEN** an override with a category, a note and the tags `trip` and `family` is saved and read back
- **THEN** the same category, note and tags in the same order are returned

#### Scenario: No override
- **WHEN** an override is read for a transaction that has none
- **THEN** no override is returned
