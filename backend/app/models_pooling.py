"""Tables for group-buying pools.

Kept in their own module so the feature is reviewable as a unit. All money is
stored as integer paise -- never float -- matching the domain layer in
``app/services/pooling``.

The domain class ``pooling.Pool`` and the table ``BuyingPool`` are deliberately
different types: the table is storage, the domain object is the thing that
knows how to price and settle. The repository maps between them.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Supplier(SQLModel, table=True):
    __tablename__ = "supplier"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str = ""


class PriceList(SQLModel, table=True):
    """A versioned tier table for one supplier SKU.

    Supplier prices change; a settled pool must keep pointing at the exact
    list it was priced against, so these rows are never updated in place -- a
    new version is inserted and the old one gets a ``valid_to``.
    """

    __tablename__ = "price_list"
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    sku: str = Field(index=True)
    version: str
    valid_from: str  # YYYY-MM-DD
    valid_to: Optional[str] = None


class PriceTier(SQLModel, table=True):
    __tablename__ = "price_tier"
    id: Optional[int] = Field(default=None, primary_key=True)
    price_list_id: int = Field(foreign_key="price_list.id", index=True)
    min_qty: int
    max_qty: Optional[int] = None  # None = unbounded top tier
    unit_price: int  # paise


class BuyingPool(SQLModel, table=True):
    __tablename__ = "buying_pool"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    status: str = Field(default="draft", index=True)
    #: Only decides who gets a leftover paisa on a tie, so the advantage
    #: rotates across a recurring series instead of always landing on one store.
    rotation: int = 0
    strategy: str = Field(default="pro_rata")
    closes_at: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settled_at: Optional[datetime] = None


class PoolProduct(SQLModel, table=True):
    """Which SKUs a pool buys, pinned to the price list it will settle against."""

    __tablename__ = "pool_product"
    id: Optional[int] = Field(default=None, primary_key=True)
    pool_id: int = Field(foreign_key="buying_pool.id", index=True)
    sku: str = Field(index=True)
    price_list_id: int = Field(foreign_key="price_list.id")


class PoolOrder(SQLModel, table=True):
    __tablename__ = "pool_order"
    id: Optional[int] = Field(default=None, primary_key=True)
    pool_id: int = Field(foreign_key="buying_pool.id", index=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    sku: str = Field(index=True)
    qty: int
    committed_at: datetime = Field(default_factory=datetime.utcnow)


class PoolSettlementLine(SQLModel, table=True):
    """What each store actually owed when the pool closed.

    Written once at settlement so the final numbers survive any later change
    to price lists or orders.
    """

    __tablename__ = "pool_settlement_line"
    id: Optional[int] = Field(default=None, primary_key=True)
    pool_id: int = Field(foreign_key="buying_pool.id", index=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    sku: str
    qty: int
    price_list_version: str
    cost_alone: int      # paise
    payable: int         # paise
    savings: int         # paise
    strategy: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PoolEvent(SQLModel, table=True):
    """Append-only audit trail.

    Every state change lands here with who did it and when, so a dispute can
    be answered by reconstructing what the pool looked like at any moment
    rather than by arguing about it.
    """

    __tablename__ = "pool_event"
    id: Optional[int] = Field(default=None, primary_key=True)
    pool_id: int = Field(foreign_key="buying_pool.id", index=True)
    actor: str  # store code, or "system"
    kind: str = Field(index=True)  # opened | ordered | withdrew | locked | settled | cancelled
    detail: str = ""  # JSON blob, free-form per kind
    created_at: datetime = Field(default_factory=datetime.utcnow)
