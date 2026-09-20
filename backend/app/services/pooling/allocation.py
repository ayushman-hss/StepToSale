"""Splitting a pool's savings between its members, to the last paisa.

Two rules are offered because they answer different questions:

``pro_rata``   -- split in proportion to how much each store ordered. Simple,
                 easy to explain, and what most buying groups actually use.
``shapley``    -- split by each store's average marginal contribution across
                 every possible coalition. Costlier to compute but it is the
                 fair answer when one store's volume is what tips the tier and
                 a pro-rata split would let the others free-ride on it.

Both return integers that sum to exactly the amount being divided. That is
enforced, not hoped for: the alternative is a settlement that quietly loses or
invents paise.
"""
from __future__ import annotations

from fractions import Fraction
from math import factorial
from typing import Callable, Mapping, Sequence

__all__ = [
    "AllocationError",
    "largest_remainder",
    "pro_rata",
    "shapley_values",
    "shapley_allocation",
    "MAX_SHAPLEY_MEMBERS",
]

# 2**n coalitions are enumerated. Twelve stores is 4096 -- instant, and far
# beyond any real neighbourhood pool. Past that, pro_rata is the honest answer.
MAX_SHAPLEY_MEMBERS = 12


class AllocationError(ValueError):
    """Raised when an amount cannot be divided as asked."""


def _round_to_ints(
    exact: Sequence[Fraction], total: int, rotation: int = 0
) -> list[int]:
    """Round exact shares to ints that still sum to ``total``.

    Largest-remainder: floor everything, then hand the leftover units to the
    largest fractional parts.

    Ties are broken on index so a settlement is reproducible -- but a fixed
    index means two members with identical shares would see the same one
    collect the spare paisa in every pool they ever run. ``rotation`` (a pool
    sequence number, say) shifts where tie-breaking starts, so the advantage
    moves around instead of accruing to whoever sorts first.
    """
    if sum(exact) != total:
        raise AllocationError(
            f"shares sum to {sum(exact)} but total is {total}"
        )

    floors = [int(share // 1) for share in exact]
    leftover = total - sum(floors)
    if leftover == 0:
        return floors

    n = len(exact)
    order = sorted(
        range(n),
        key=lambda i: (-(exact[i] - floors[i]), (i - rotation) % n),
    )
    step = 1 if leftover > 0 else -1
    for i in order[: abs(leftover)]:
        floors[i] += step
    return floors


def largest_remainder(
    total: int, weights: Sequence[int], rotation: int = 0
) -> list[int]:
    """Split ``total`` across ``weights``, summing to exactly ``total``."""
    if isinstance(total, bool) or not isinstance(total, int):
        raise AllocationError(f"total must be an int, got {total!r}")
    if total < 0:
        raise AllocationError(f"total must be >= 0, got {total}")
    if any(isinstance(w, bool) or not isinstance(w, int) for w in weights):
        raise AllocationError("weights must be ints")
    if any(w < 0 for w in weights):
        raise AllocationError("weights must be >= 0")

    if not weights:
        if total:
            raise AllocationError(f"cannot split {total} across zero parties")
        return []

    denominator = sum(weights)
    if denominator == 0:
        if total:
            raise AllocationError(
                f"cannot split {total} when every weight is zero"
            )
        return [0] * len(weights)

    exact = [Fraction(total * w, denominator) for w in weights]
    return _round_to_ints(exact, total, rotation)


def pro_rata(
    total: int, quantities: Mapping[str, int], rotation: int = 0
) -> dict[str, int]:
    """Split ``total`` in proportion to each member's quantity."""
    keys = list(quantities)
    parts = largest_remainder(total, [quantities[k] for k in keys], rotation)
    return dict(zip(keys, parts))


def shapley_values(
    members: Sequence[str],
    value_of: Callable[[frozenset[str]], int],
) -> dict[str, Fraction]:
    """Exact Shapley value per member for the cooperative game ``value_of``.

    ``value_of`` is the surplus a coalition creates together; it must return 0
    for the empty coalition. Results are Fractions, so they are exact and sum
    to ``value_of(everyone)``.
    """
    unique = list(dict.fromkeys(members))
    if len(unique) != len(members):
        raise AllocationError("members must be distinct")
    n = len(unique)
    if n == 0:
        return {}
    if n > MAX_SHAPLEY_MEMBERS:
        raise AllocationError(
            f"shapley is capped at {MAX_SHAPLEY_MEMBERS} members "
            f"({n} requested); use pro_rata for a pool this large"
        )

    # Precompute the coalition value for every bitmask once.
    values: list[int] = [0] * (1 << n)
    for mask in range(1 << n):
        coalition = frozenset(unique[i] for i in range(n) if mask >> i & 1)
        values[mask] = value_of(coalition)
    if values[0] != 0:
        raise AllocationError(
            f"the empty coalition must be worth 0, got {values[0]}"
        )

    weights = [
        Fraction(factorial(size) * factorial(n - size - 1), factorial(n))
        for size in range(n)
    ]

    result: dict[str, Fraction] = {}
    for i, name in enumerate(unique):
        bit = 1 << i
        total = Fraction(0)
        for mask in range(1 << n):
            if mask & bit:
                continue
            size = bin(mask).count("1")
            total += weights[size] * (values[mask | bit] - values[mask])
        result[name] = total
    return result


def shapley_allocation(
    members: Sequence[str],
    value_of: Callable[[frozenset[str]], int],
    rotation: int = 0,
) -> dict[str, int]:
    """Shapley split rounded to whole paise, summing to the grand coalition."""
    exact = shapley_values(members, value_of)
    if not exact:
        return {}
    grand = value_of(frozenset(exact))
    keys = list(exact)
    parts = _round_to_ints([exact[k] for k in keys], grand, rotation)
    return dict(zip(keys, parts))
