"""Mapping between the pooling tables and the pure domain objects.

The domain layer knows nothing about SQL; this module is the only place the
two meet. Loading rebuilds a ``Pool`` through its own public API so the same
validation applies to stored data as to fresh input.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from ...models import Store
from ...models_pooling import (
    BuyingPool,
    PoolEvent,
    PoolOrder,
    PoolProduct,
    PoolSettlementLine,
    PriceList,
    PriceTier,
    Supplier,
)
from .pool import Pool, PoolStatus, Settlement, Strategy
from .tiers import Tier, TierTable

__all__ = [
    "RepositoryError",
    "load_tier_table",
    "load_pool",
    "record_event",
    "persist_settlement",
    "store_ids_by_code",
]


class RepositoryError(RuntimeError):
    pass


def store_ids_by_code(session: Session) -> dict[str, int]:
    return {s.code: s.id for s in session.exec(select(Store)).all() if s.id}


def _store_codes_by_id(session: Session) -> dict[int, str]:
    return {s.id: s.code for s in session.exec(select(Store)).all() if s.id}


def load_tier_table(session: Session, price_list_id: int) -> TierTable:
    pl = session.get(PriceList, price_list_id)
    if pl is None:
        raise RepositoryError(f"price list {price_list_id} not found")
    supplier_code = session.exec(
        select(Supplier.code).where(Supplier.id == pl.supplier_id)
    ).first()
    rows = session.exec(
        select(PriceTier)
        .where(PriceTier.price_list_id == price_list_id)
        .order_by(PriceTier.min_qty)
    ).all()
    if not rows:
        raise RepositoryError(f"price list {pl.version} for {pl.sku} has no tiers")
    return TierTable(
        supplier_id=supplier_code or str(pl.supplier_id),
        sku=pl.sku,
        version=pl.version,
        tiers=tuple(Tier(r.min_qty, r.max_qty, r.unit_price) for r in rows),
    )


def load_pool(session: Session, code: str) -> tuple[Pool, BuyingPool]:
    """Rebuild the domain pool for ``code``, plus the row it came from."""
    row = session.exec(select(BuyingPool).where(BuyingPool.code == code)).first()
    if row is None:
        raise RepositoryError(f"no pool named {code!r}")

    products = session.exec(
        select(PoolProduct).where(PoolProduct.pool_id == row.id)
    ).all()
    price_lists = {
        p.sku: load_tier_table(session, p.price_list_id) for p in products
    }

    domain = Pool(
        pool_id=row.code,
        name=row.name,
        price_lists=price_lists,
        rotation=row.rotation,
    )

    # Orders are replayed through place_order so stored rows face the same
    # validation as fresh ones; the real status is applied afterwards.
    domain.status = PoolStatus.OPEN
    codes = _store_codes_by_id(session)
    orders = session.exec(select(PoolOrder).where(PoolOrder.pool_id == row.id)).all()
    for o in orders:
        store_code = codes.get(o.store_id)
        if store_code is None:
            raise RepositoryError(f"order {o.id} points at a missing store")
        domain.place_order(store_code, o.sku, o.qty)

    domain.status = PoolStatus(row.status)
    return domain, row


def record_event(
    session: Session,
    pool_id: int,
    actor: str,
    kind: str,
    **detail: object,
) -> PoolEvent:
    """Append to the audit trail. Never updated, only inserted."""
    event = PoolEvent(
        pool_id=pool_id,
        actor=actor,
        kind=kind,
        detail=json.dumps(detail, default=str, sort_keys=True),
    )
    session.add(event)
    return event


def persist_settlement(
    session: Session,
    row: BuyingPool,
    settlement: Settlement,
    strategy: Strategy,
) -> None:
    """Freeze the closing numbers so later price changes cannot rewrite them."""
    ids = store_ids_by_code(session)
    for product in settlement.products:
        for store_code, qty in product.qty_by_store.items():
            store_id = ids.get(store_code)
            if store_id is None:
                raise RepositoryError(f"unknown store {store_code!r} at settlement")
            session.add(
                PoolSettlementLine(
                    pool_id=row.id,
                    store_id=store_id,
                    sku=product.sku,
                    qty=qty,
                    price_list_version=product.price_list_version,
                    cost_alone=product.cost_alone_by_store[store_code],
                    payable=product.payable_by_store[store_code],
                    savings=product.savings_by_store[store_code],
                    strategy=strategy.value,
                )
            )
    row.status = PoolStatus.SETTLED.value
    row.strategy = strategy.value
    row.settled_at = datetime.now(timezone.utc)
    session.add(row)
    record_event(
        session,
        row.id,
        actor="system",
        kind="settled",
        strategy=strategy.value,
        invoice_total=settlement.invoice_total,
        total_savings=settlement.total_savings,
    )
