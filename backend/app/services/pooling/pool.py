"""The pool itself: who ordered what, which tier that reaches, who saved.

Pure domain logic -- no database, no framework. A pool moves through an
explicit lifecycle and refuses transitions that a real buying group would
refuse, and every settlement is checked to balance against the supplier
invoice before it is returned.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .allocation import pro_rata, shapley_allocation
from .tiers import TierTable

__all__ = [
    "PoolStatus",
    "Strategy",
    "PoolError",
    "ProductSettlement",
    "StoreSettlement",
    "Settlement",
    "Pool",
]


class PoolError(RuntimeError):
    """Raised on an action the pool's current state does not permit."""


class PoolStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    LOCKED = "locked"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class Strategy(str, Enum):
    #: Everyone simply pays the pooled unit price. No redistribution, so a
    #: store already in the cheap tier alone saves nothing while smaller
    #: stores ride on its volume.
    UNIT_PRICE = "unit_price"
    #: Total savings split in proportion to quantity ordered.
    PRO_RATA = "pro_rata"
    #: Total savings split by average marginal contribution.
    SHAPLEY = "shapley"


_TRANSITIONS: dict[PoolStatus, frozenset[PoolStatus]] = {
    PoolStatus.DRAFT: frozenset({PoolStatus.OPEN, PoolStatus.CANCELLED}),
    PoolStatus.OPEN: frozenset({PoolStatus.LOCKED, PoolStatus.CANCELLED}),
    PoolStatus.LOCKED: frozenset(
        {PoolStatus.SETTLED, PoolStatus.OPEN, PoolStatus.CANCELLED}
    ),
    PoolStatus.SETTLED: frozenset(),
    PoolStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class ProductSettlement:
    sku: str
    supplier_id: str
    price_list_version: str
    total_qty: int
    pooled_unit_price: int
    tier_label: str
    units_to_next_tier: int | None
    next_tier_unit_price: int | None
    qty_by_store: Mapping[str, int]
    cost_alone_by_store: Mapping[str, int]
    payable_by_store: Mapping[str, int]
    savings_by_store: Mapping[str, int]
    invoice_total: int
    total_savings: int


@dataclass(frozen=True)
class StoreSettlement:
    store: str
    cost_alone: int
    payable: int
    savings: int

    @property
    def savings_pct(self) -> float:
        """Display only -- never feed this back into money arithmetic."""
        return (self.savings / self.cost_alone * 100) if self.cost_alone else 0.0


@dataclass(frozen=True)
class Settlement:
    pool_id: str
    strategy: Strategy
    products: tuple[ProductSettlement, ...]
    stores: tuple[StoreSettlement, ...]
    invoice_total: int
    total_savings: int


@dataclass
class Pool:
    """A group order. Quantities are whole units; money is integer paise."""

    pool_id: str
    name: str
    price_lists: Mapping[str, TierTable]
    status: PoolStatus = PoolStatus.DRAFT
    #: Sequence number of this pool in a recurring series. Only affects who
    #: receives a leftover paisa when shares tie, so the advantage rotates
    #: instead of always landing on the same member.
    rotation: int = 0
    _orders: dict[tuple[str, str], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for sku, table in self.price_lists.items():
            if not isinstance(table, TierTable):
                raise PoolError(f"price list for {sku!r} is not a TierTable")
            if table.sku != sku:
                raise PoolError(
                    f"price list keyed {sku!r} but describes {table.sku!r}"
                )

    # -- lifecycle ----------------------------------------------------
    def _transition(self, to: PoolStatus) -> None:
        if to not in _TRANSITIONS[self.status]:
            raise PoolError(f"cannot go from {self.status.value} to {to.value}")
        self.status = to

    def open(self) -> None:
        self._transition(PoolStatus.OPEN)

    def lock(self) -> None:
        self._transition(PoolStatus.LOCKED)

    def unlock(self) -> None:
        if self.status is not PoolStatus.LOCKED:
            raise PoolError(f"cannot unlock a {self.status.value} pool")
        self._transition(PoolStatus.OPEN)

    def cancel(self) -> None:
        self._transition(PoolStatus.CANCELLED)

    # -- orders -------------------------------------------------------
    def place_order(self, store: str, sku: str, qty: int) -> None:
        """Set ``store``'s quantity for ``sku``. Replaces any earlier figure."""
        if self.status is not PoolStatus.OPEN:
            raise PoolError(
                f"pool is {self.status.value}; orders need an open pool"
            )
        if sku not in self.price_lists:
            raise PoolError(f"no supplier price list for {sku!r}")
        if isinstance(qty, bool) or not isinstance(qty, int):
            raise PoolError(f"qty must be an int, got {qty!r}")
        if qty < 1:
            raise PoolError(
                f"qty must be >= 1, got {qty}; use withdraw() to leave"
            )
        if not store:
            raise PoolError("store code must not be empty")
        self._orders[(store, sku)] = qty

    def withdraw(self, store: str, sku: str | None = None) -> None:
        """Remove one line, or the store's whole order when ``sku`` is None."""
        if self.status is not PoolStatus.OPEN:
            raise PoolError(f"pool is {self.status.value}; cannot withdraw")
        keys = [
            k
            for k in self._orders
            if k[0] == store and (sku is None or k[1] == sku)
        ]
        if not keys:
            raise PoolError(f"{store!r} has no matching order to withdraw")
        for k in keys:
            del self._orders[k]

    @property
    def orders(self) -> Mapping[tuple[str, str], int]:
        return dict(self._orders)

    @property
    def stores(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(store for store, _ in self._orders))

    def qty_by_store(self, sku: str) -> dict[str, int]:
        return {
            store: qty
            for (store, s), qty in self._orders.items()
            if s == sku and qty > 0
        }

    # -- settlement ---------------------------------------------------
    def _settle_product(self, sku: str, strategy: Strategy) -> ProductSettlement:
        table = self.price_lists[sku]
        quantities = self.qty_by_store(sku)
        stores = list(quantities)
        total_qty = sum(quantities.values())

        cost_alone = {s: table.cost_for(q) for s, q in quantities.items()}
        invoice_total = table.cost_for(total_qty)
        total_savings = sum(cost_alone.values()) - invoice_total
        # Guaranteed by TierTable's non-increasing price rule, but a pool that
        # somehow costs more than buying alone must never be settled silently.
        if total_savings < 0:
            raise PoolError(
                f"pooling {sku!r} costs {-total_savings} paise more than buying "
                "alone; refusing to settle"
            )

        if not stores:
            savings: dict[str, int] = {}
        elif strategy is Strategy.UNIT_PRICE:
            unit = table.unit_price_for(total_qty)
            savings = {s: cost_alone[s] - unit * quantities[s] for s in stores}
        elif strategy is Strategy.PRO_RATA:
            savings = pro_rata(total_savings, quantities, self.rotation)
        elif strategy is Strategy.SHAPLEY:

            def value_of(coalition: frozenset[str]) -> int:
                if not coalition:
                    return 0
                alone = sum(cost_alone[s] for s in coalition)
                together = table.cost_for(
                    sum(quantities[s] for s in coalition)
                )
                return alone - together

            savings = shapley_allocation(stores, value_of, self.rotation)
        else:  # pragma: no cover -- Strategy is exhaustive
            raise PoolError(f"unknown strategy {strategy!r}")

        payable = {s: cost_alone[s] - savings[s] for s in stores}

        if sum(savings.values()) != total_savings:
            raise PoolError(
                f"{sku}: savings split to {sum(savings.values())} but pool "
                f"saved {total_savings}"
            )
        if sum(payable.values()) != invoice_total:
            raise PoolError(
                f"{sku}: stores owe {sum(payable.values())} but the supplier "
                f"invoice is {invoice_total}"
            )

        tier = table.tier_for(total_qty) if total_qty else None
        nxt = table.next_tier(total_qty) if total_qty else None
        return ProductSettlement(
            sku=sku,
            supplier_id=table.supplier_id,
            price_list_version=table.version,
            total_qty=total_qty,
            pooled_unit_price=tier.unit_price if tier else 0,
            tier_label=tier.label if tier else "-",
            units_to_next_tier=(
                table.units_to_next_tier(total_qty) if total_qty else None
            ),
            next_tier_unit_price=nxt.unit_price if nxt else None,
            qty_by_store=quantities,
            cost_alone_by_store=cost_alone,
            payable_by_store=payable,
            savings_by_store=savings,
            invoice_total=invoice_total,
            total_savings=total_savings,
        )

    def project(self, strategy: Strategy = Strategy.PRO_RATA) -> Settlement:
        """Settlement as it stands right now, without changing the pool.

        Shapley is additive across independent games, so computing it per
        product and summing gives the same answer as one combined game.
        """
        if self.status is PoolStatus.CANCELLED:
            raise PoolError("a cancelled pool has nothing to settle")

        skus = sorted({sku for _, sku in self._orders})
        products = tuple(self._settle_product(sku, strategy) for sku in skus)

        per_store: dict[str, list[int]] = {}
        for p in products:
            for store in p.qty_by_store:
                acc = per_store.setdefault(store, [0, 0, 0])
                acc[0] += p.cost_alone_by_store[store]
                acc[1] += p.payable_by_store[store]
                acc[2] += p.savings_by_store[store]

        stores = tuple(
            StoreSettlement(store=s, cost_alone=v[0], payable=v[1], savings=v[2])
            for s, v in sorted(per_store.items())
        )
        invoice_total = sum(p.invoice_total for p in products)
        total_savings = sum(p.total_savings for p in products)

        if sum(s.payable for s in stores) != invoice_total:
            raise PoolError("pool total does not balance against the invoice")
        if sum(s.savings for s in stores) != total_savings:
            raise PoolError("pool savings do not balance")

        return Settlement(
            pool_id=self.pool_id,
            strategy=strategy,
            products=products,
            stores=stores,
            invoice_total=invoice_total,
            total_savings=total_savings,
        )

    def settle(self, strategy: Strategy = Strategy.PRO_RATA) -> Settlement:
        """Final settlement. Only a locked pool can be settled, exactly once."""
        if self.status is not PoolStatus.LOCKED:
            raise PoolError(f"pool is {self.status.value}; lock it before settling")
        if not self._orders:
            raise PoolError("cannot settle a pool with no orders")
        result = self.project(strategy)
        self._transition(PoolStatus.SETTLED)
        return result

    def close(self, strategy: Strategy = Strategy.PRO_RATA) -> Settlement:
        """Lock and settle in one step -- the UI's 'close pool' action."""
        self.lock()
        try:
            return self.settle(strategy)
        except PoolError:
            self.unlock()
            raise
