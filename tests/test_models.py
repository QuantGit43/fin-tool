import pytest

from fin.models import Transaction


def make_txn(**changes):
    fields = dict(
        bank="mono",
        account_id="acc-1",
        txn_id="t-1",
        ts=1767225600,
        amount=-12345,
        currency="UAH",
        description="Grocery store",
        raw="{}",
    )
    fields.update(changes)
    return Transaction(**fields)


def test_fractional_amount_is_rejected():
    with pytest.raises(TypeError, match="amount"):
        make_txn(amount=123.45)


@pytest.mark.parametrize("field", ["amount", "ts"])
@pytest.mark.parametrize("value", [True, False])
def test_boolean_is_not_a_number(field, value):
    with pytest.raises(TypeError, match=field):
        make_txn(**{field: value})
