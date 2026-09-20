"""Group-buying pools: stores combine orders to reach volume price tiers.

Pure domain layer -- deliberately free of database and framework imports so it
can be exercised in isolation. Nothing here is wired into the running app yet.
"""
from .money import MoneyError, format_paise, to_paise
from .tiers import Tier, TierError, TierTable
from .allocation import (
    AllocationError,
    largest_remainder,
    pro_rata,
    shapley_allocation,
    shapley_values,
)
from .pool import (
    Pool,
    PoolError,
    PoolStatus,
    ProductSettlement,
    Settlement,
    StoreSettlement,
    Strategy,
)

__all__ = [
    "MoneyError", "format_paise", "to_paise",
    "Tier", "TierError", "TierTable",
    "AllocationError", "largest_remainder", "pro_rata",
    "shapley_allocation", "shapley_values",
    "Pool", "PoolError", "PoolStatus", "ProductSettlement",
    "Settlement", "StoreSettlement", "Strategy",
]
