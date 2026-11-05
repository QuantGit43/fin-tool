"""Plain data objects shared by sources, storage and reports.

Money is always an integer number of minor currency units (kopecks, cents);
time is always integer UTC epoch seconds.
"""

from dataclasses import dataclass

ACCOUNT_KINDS = ("card", "jar", "file")


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

    def __post_init__(self):
        if self.kind not in ACCOUNT_KINDS:
            raise ValueError(f"kind must be one of {ACCOUNT_KINDS}, got {self.kind!r}")
        if self.goal is not None and self.kind != "jar":
            raise ValueError("goal is only allowed for jars")
        for name in ("balance", "goal"):
            value = getattr(self, name)
            if value is not None:
                _require_int(name, value)


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
        if (self.operation_amount is None) != (self.operation_currency is None):
            raise ValueError("operation_amount and operation_currency must be given together")
        if self.operation_amount is not None:
            _require_int("operation_amount", self.operation_amount)


@dataclass(frozen=True)
class Override:
    bank: str
    txn_id: str
    updated_at: int
    category: str | None = None
    note: str | None = None
    tags: tuple[str, ...] = ()
    source: str = "user"
