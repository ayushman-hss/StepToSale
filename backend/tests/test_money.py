from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from app.services.pooling.money import MoneyError, format_paise, to_paise


class TestToPaise:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (45, 4500),
            (0, 0),
            ("35.50", 3550),
            ("0.01", 1),
            ("0.10", 10),
            (Decimal("12.34"), 1234),
            (Decimal("1000000"), 100_000_000),
            ("-5.25", -525),
        ],
    )
    def test_exact_conversions(self, value, expected):
        assert to_paise(value) == expected

    @pytest.mark.parametrize("value", [45.5, 0.1, 1e10, float("nan"), float("inf")])
    def test_floats_are_refused(self, value):
        # Refusing float is the whole point: 0.1 + 0.2 != 0.3 and a settlement
        # built on that loses paise far from the cause.
        with pytest.raises(MoneyError, match="refusing float"):
            to_paise(value)

    @pytest.mark.parametrize("value", [True, False])
    def test_bool_is_not_money(self, value):
        with pytest.raises(MoneyError):
            to_paise(value)

    @pytest.mark.parametrize("value", ["1.005", "0.001", Decimal("0.0001")])
    def test_sub_paisa_precision_is_refused(self, value):
        with pytest.raises(MoneyError, match="finer than one paisa"):
            to_paise(value)

    @pytest.mark.parametrize("value", ["abc", "", None, object()])
    def test_nonsense_is_refused(self, value):
        with pytest.raises(MoneyError):
            to_paise(value)

    def test_non_finite_decimal_is_refused(self):
        with pytest.raises(MoneyError, match="finite"):
            to_paise(Decimal("NaN"))


class TestFormatPaise:
    @pytest.mark.parametrize(
        "paise,expected",
        [
            (0, "₹0.00"),
            (1, "₹0.01"),
            (4500, "₹45.00"),
            (123456, "₹1,234.56"),
            (-500, "-₹5.00"),
            (-1, "-₹0.01"),
            (100_000_000, "₹1,000,000.00"),
        ],
    )
    def test_formatting(self, paise, expected):
        assert format_paise(paise) == expected

    @pytest.mark.parametrize("bad", [45.0, "100", None, True])
    def test_requires_int(self, bad):
        with pytest.raises(MoneyError):
            format_paise(bad)


@given(st.integers(min_value=-10**12, max_value=10**12))
def test_int_rupees_roundtrip(rupees):
    assert to_paise(rupees) == rupees * 100


@given(st.integers(min_value=-10**12, max_value=10**12))
def test_format_never_crashes_and_keeps_sign(paise):
    out = format_paise(paise)
    assert out.startswith("-") == (paise < 0)
    assert "₹" in out
