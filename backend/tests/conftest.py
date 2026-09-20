import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.pooling import Tier, TierTable  # noqa: E402


@pytest.fixture
def sugar() -> TierTable:
    """The price list from the spec: 1-19 @45, 20-49 @40, 50+ @35."""
    return TierTable(
        "SUP1",
        "SUGAR",
        "2026-09-01",
        (Tier(1, 19, 4500), Tier(20, 49, 4000), Tier(50, None, 3500)),
    )


@pytest.fixture
def rice() -> TierTable:
    return TierTable(
        "SUP2",
        "RICE",
        "2026-09-01",
        (Tier(1, 24, 6200), Tier(25, None, 5800)),
    )


@pytest.fixture
def flat() -> TierTable:
    """A supplier with no volume discount at all."""
    return TierTable("SUP3", "SALT", "v1", (Tier(1, None, 2000),))
