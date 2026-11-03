import pytest

from tests.factories import make_account, make_txn


def test_unknown_account_kind_is_rejected():
    with pytest.raises(ValueError, match="kind"):
        make_account(kind="deposit")


def test_goal_only_for_jars():
    with pytest.raises(ValueError, match="goal"):
        make_account(kind="card", goal=100000)


def test_jar_with_goal_is_accepted():
    jar = make_account(kind="jar", currency="USD", balance=35000, goal=100000)
    assert jar.goal == 100000


@pytest.mark.parametrize("field", ["balance", "goal"])
@pytest.mark.parametrize("value", [12.5, True])
def test_fractional_balance_or_goal_is_rejected(field, value):
    with pytest.raises(TypeError, match=field):
        make_account(kind="jar", **{field: value})


def test_fractional_amount_is_rejected():
    with pytest.raises(TypeError, match="amount"):
        make_txn(amount=123.45)


@pytest.mark.parametrize(
    "changes",
    [{"operation_amount": -2000}, {"operation_currency": "EUR"}],
)
def test_incomplete_operation_currency_is_rejected(changes):
    with pytest.raises(ValueError, match="operation"):
        make_txn(**changes)


def test_operation_amount_must_be_integer():
    with pytest.raises(TypeError, match="operation_amount"):
        make_txn(operation_amount=20.5, operation_currency="EUR")


@pytest.mark.parametrize("field", ["amount", "ts"])
@pytest.mark.parametrize("value", [True, False])
def test_boolean_is_not_a_number(field, value):
    with pytest.raises(TypeError, match=field):
        make_txn(**{field: value})
