"""Supplier tiered price lists, and the snapshot a settlement is pinned to.

A tier table is validated on construction: real supplier price lists are
contiguous, start at one unit, end unbounded, and get cheaper with volume.
Rejecting a malformed table here means the settlement maths downstream can
assume pooling never costs more than buying alone.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Tier", "TierTable", "TierError"]


class TierError(ValueError):
    """Raised when a price list could not describe a real supplier."""


def _check_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TierError(f"{name} must be an int, got {value!r}")
    return value


@dataclass(frozen=True)
class Tier:
    min_qty: int
    max_qty: int | None  # inclusive; None means unbounded
    unit_price: int      # paise per unit

    def __post_init__(self) -> None:
        _check_int("min_qty", self.min_qty)
        _check_int("unit_price", self.unit_price)
        if self.max_qty is not None:
            _check_int("max_qty", self.max_qty)
        if self.min_qty < 1:
            raise TierError(f"min_qty must be >= 1, got {self.min_qty}")
        if self.max_qty is not None and self.max_qty < self.min_qty:
            raise TierError(f"tier {self.min_qty}-{self.max_qty} is inverted")
        if self.unit_price <= 0:
            raise TierError(f"unit_price must be > 0, got {self.unit_price}")

    def covers(self, qty: int) -> bool:
        if qty < self.min_qty:
            return False
        return self.max_qty is None or qty <= self.max_qty

    @property
    def label(self) -> str:
        return f"{self.min_qty}+" if self.max_qty is None else f"{self.min_qty}-{self.max_qty}"


@dataclass(frozen=True)
class TierTable:
    """An immutable, versioned price list for one supplier SKU.

    ``version`` exists so a closed pool can record exactly which price list it
    settled against. Supplier prices change; a settlement must not.
    """

    supplier_id: str
    sku: str
    version: str
    tiers: tuple[Tier, ...]

    def __post_init__(self) -> None:
        if not self.tiers:
            raise TierError("a price list needs at least one tier")
        if not all(isinstance(t, Tier) for t in self.tiers):
            raise TierError("tiers must be Tier instances")

        ordered = sorted(self.tiers, key=lambda t: t.min_qty)
        if list(ordered) != list(self.tiers):
            raise TierError("tiers must be listed in ascending quantity order")

        if self.tiers[0].min_qty != 1:
            raise TierError(
                f"price list must start at qty 1, starts at {self.tiers[0].min_qty}"
            )
        if self.tiers[-1].max_qty is not None:
            raise TierError("the last tier must be unbounded (max_qty=None)")

        for lower, upper in zip(self.tiers, self.tiers[1:]):
            if lower.max_qty is None:
                raise TierError("only the last tier may be unbounded")
            if lower.max_qty + 1 != upper.min_qty:
                gap = "gap" if lower.max_qty + 1 < upper.min_qty else "overlap"
                raise TierError(
                    f"{gap} between tiers {lower.label} and {upper.label}"
                )
            if upper.unit_price > lower.unit_price:
                raise TierError(
                    f"tier {upper.label} costs more per unit than {lower.label}; "
                    "pooling must never be a penalty"
                )

    def tier_for(self, qty: int) -> Tier:
        _check_int("qty", qty)
        if qty < 1:
            raise TierError(f"qty must be >= 1 to price a tier, got {qty}")
        for tier in self.tiers:
            if tier.covers(qty):
                return tier
        raise TierError(f"no tier covers qty {qty}")  # unreachable if validated

    def unit_price_for(self, qty: int) -> int:
        return self.tier_for(qty).unit_price

    def cost_for(self, qty: int) -> int:
        """Total paise for ``qty`` units bought in one order. qty 0 costs 0."""
        _check_int("qty", qty)
        if qty < 0:
            raise TierError(f"qty must be >= 0, got {qty}")
        if qty == 0:
            return 0
        return self.unit_price_for(qty) * qty

    def next_tier(self, qty: int) -> Tier | None:
        """The next cheaper tier above ``qty``, or None if already cheapest."""
        current = self.tier_for(qty) if qty >= 1 else None
        for tier in self.tiers:
            if tier.min_qty > qty and (current is None or tier.unit_price < current.unit_price):
                return tier
        return None

    def units_to_next_tier(self, qty: int) -> int | None:
        nxt = self.next_tier(qty)
        return None if nxt is None else nxt.min_qty - qty
