"""Money as integer paise.

Every amount in the pooling system is an ``int`` number of paise. Floats are
rejected at the boundary rather than tolerated: a settlement that splits a
discount across stores has to add up exactly, and binary floating point
cannot promise that. ``Decimal`` and ``str`` are the accepted inputs.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

__all__ = ["to_paise", "format_paise", "MoneyError"]


class MoneyError(ValueError):
    """Raised when a value cannot be represented exactly as paise."""


def to_paise(value: Decimal | str | int) -> int:
    """Convert rupees to integer paise, exactly.

    ``float`` is refused on purpose -- 0.1 + 0.2 is not 0.3, and a settlement
    built on that will lose paise that the invariants then catch far from the
    cause. Pass a ``Decimal`` or a string instead.
    """
    if isinstance(value, bool):
        raise MoneyError(f"bool is not a monetary amount: {value!r}")
    if isinstance(value, float):
        raise MoneyError(
            f"refusing float {value!r}: pass Decimal(str(x)) or a string "
            "so the amount is exact"
        )
    if isinstance(value, int):
        return value * 100

    if isinstance(value, str):
        try:
            dec = Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise MoneyError(f"not a monetary amount: {value!r}") from exc
    elif isinstance(value, Decimal):
        dec = value
    else:
        raise MoneyError(f"not a monetary amount: {value!r}")

    if not dec.is_finite():
        raise MoneyError(f"not a finite amount: {value!r}")

    shifted = dec * 100
    rounded = shifted.to_integral_value(rounding=ROUND_HALF_UP)
    if shifted != rounded:
        raise MoneyError(
            f"{value!r} is finer than one paisa; round it before converting"
        )
    return int(rounded)


def format_paise(paise: int) -> str:
    """Render paise as rupees for display only -- never for arithmetic."""
    if not isinstance(paise, int) or isinstance(paise, bool):
        raise MoneyError(f"expected int paise, got {paise!r}")
    sign = "-" if paise < 0 else ""
    whole, part = divmod(abs(paise), 100)
    return f"{sign}₹{whole:,}.{part:02d}"
