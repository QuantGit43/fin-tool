"""Plain data objects shared by sources, storage and reports.

Money is always an integer number of minor currency units (kopecks, cents);
time is always integer UTC epoch seconds.
"""

from dataclasses import dataclass


def _require_int(name, value):
    # bool is a subclass of int in Python, so True would otherwise pass as 1
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, got {value!r}")


@dataclass(frozen=True)
class Account:
    bank: str
    account_id: str
    kind: str
    currency: str
    title: str
    balance: int | None = None
    goal: int | None = None


@dataclass(frozen=True)
class Transaction:
    bank: str
    account_id: str
    txn_id: str
    ts: int
    amount: int
    currency: str
    description: str
    raw: str
    mcc: int | None = None
    bank_category: str | None = None
    operation_amount: int | None = None
    operation_currency: str | None = None

    def __post_init__(self):
        _require_int("ts", self.ts)
        _require_int("amount", self.amount)


@dataclass(frozen=True)
class Override:
    bank: str
    txn_id: str
    updated_at: int
    category: str | None = None
    note: str | None = None
    tags: tuple[str, ...] = ()
    source: str = "user"
