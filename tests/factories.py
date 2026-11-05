"""Synthetic test data builders. Never put real personal data here: the repository is public."""

from fin.models import Account, Transaction


def make_account(**changes):
    fields = dict(bank="mono", account_id="acc-1", kind="card", currency="UAH", title="Black card")
    fields.update(changes)
    return Account(**fields)


def make_txn(**changes):
    fields = dict(
        bank="mono",
        account_id="acc-1",
        txn_id="t-1",
        ts=1767225600,
        amount=-12345,
        currency="UAH",
        description="Grocery store",
        raw='{"id": "t-1"}',
    )
    fields.update(changes)
    return Transaction(**fields)
