import pytest

from app.services.pooling.tiers import Tier, TierError, TierTable


class TestTierValidation:
    def test_min_qty_below_one(self):
        with pytest.raises(TierError, match="min_qty must be >= 1"):
            Tier(0, 10, 100)

    def test_inverted_range(self):
        with pytest.raises(TierError, match="inverted"):
            Tier(20, 10, 100)

    @pytest.mark.parametrize("price", [0, -1])
    def test_non_positive_price(self, price):
        with pytest.raises(TierError, match="unit_price must be > 0"):
            Tier(1, 10, price)

    @pytest.mark.parametrize("bad", [1.5, "10", True, None])
    def test_non_int_fields(self, bad):
        with pytest.raises(TierError):
            Tier(bad, 10, 100)

    def test_single_unit_tier_is_valid(self):
        assert Tier(5, 5, 100).covers(5)


class TestTierTableValidation:
    def test_empty(self):
        with pytest.raises(TierError, match="at least one tier"):
            TierTable("S", "X", "v1", ())

    def test_must_start_at_one(self):
        with pytest.raises(TierError, match="must start at qty 1"):
            TierTable("S", "X", "v1", (Tier(5, None, 100),))

    def test_last_must_be_unbounded(self):
        with pytest.raises(TierError, match="last tier must be unbounded"):
            TierTable("S", "X", "v1", (Tier(1, 10, 100),))

    def test_gap_between_tiers(self):
        with pytest.raises(TierError, match="gap between"):
            TierTable("S", "X", "v1", (Tier(1, 10, 100), Tier(20, None, 90)))

    def test_overlap_between_tiers(self):
        with pytest.raises(TierError, match="overlap between"):
            TierTable("S", "X", "v1", (Tier(1, 10, 100), Tier(8, None, 90)))

    def test_unsorted_tiers(self):
        with pytest.raises(TierError, match="ascending quantity order"):
            TierTable("S", "X", "v1", (Tier(11, None, 90), Tier(1, 10, 100)))

    def test_only_last_may_be_unbounded(self):
        with pytest.raises(TierError, match="only the last tier"):
            TierTable("S", "X", "v1", (Tier(1, None, 100), Tier(11, None, 90)))

    def test_price_must_not_increase_with_volume(self):
        # If a later tier cost more, pooling could punish members and the
        # settlement invariants downstream would no longer hold.
        with pytest.raises(TierError, match="never be a penalty"):
            TierTable("S", "X", "v1", (Tier(1, 10, 100), Tier(11, None, 120)))

    def test_equal_prices_are_allowed(self):
        table = TierTable("S", "X", "v1", (Tier(1, 10, 100), Tier(11, None, 100)))
        assert table.unit_price_for(50) == 100

    def test_single_unbounded_tier(self, flat):
        assert flat.unit_price_for(1) == flat.unit_price_for(10_000) == 2000


class TestPricing:
    @pytest.mark.parametrize(
        "qty,price", [(1, 4500), (19, 4500), (20, 4000), (49, 4000), (50, 3500), (10**6, 3500)]
    )
    def test_boundaries(self, sugar, qty, price):
        assert sugar.unit_price_for(qty) == price

    def test_cost_is_exact_multiple(self, sugar):
        assert sugar.cost_for(35) == 4000 * 35 == 140_000

    def test_zero_qty_costs_nothing(self, sugar):
        assert sugar.cost_for(0) == 0

    def test_zero_qty_has_no_tier(self, sugar):
        with pytest.raises(TierError, match="qty must be >= 1"):
            sugar.unit_price_for(0)

    def test_negative_qty(self, sugar):
        with pytest.raises(TierError, match="qty must be >= 0"):
            sugar.cost_for(-1)

    @pytest.mark.parametrize("bad", [1.0, "5", True, None])
    def test_non_int_qty(self, sugar, bad):
        with pytest.raises(TierError):
            sugar.cost_for(bad)

    def test_buying_more_can_cost_less(self, sugar):
        # A real and slightly perverse property of tiered pricing: 19kg costs
        # more in total than 20kg. Worth surfacing in the UI as advice.
        assert sugar.cost_for(19) == 85_500
        assert sugar.cost_for(20) == 80_000
        assert sugar.cost_for(20) < sugar.cost_for(19)


class TestNextTier:
    @pytest.mark.parametrize(
        "qty,units", [(1, 19), (15, 5), (19, 1), (20, 30), (49, 1)]
    )
    def test_distance_to_next_tier(self, sugar, qty, units):
        assert sugar.units_to_next_tier(qty) == units

    @pytest.mark.parametrize("qty", [50, 51, 10_000])
    def test_top_tier_has_no_next(self, sugar, qty):
        assert sugar.next_tier(qty) is None
        assert sugar.units_to_next_tier(qty) is None

    def test_flat_table_never_has_a_next_tier(self, flat):
        assert flat.next_tier(1) is None

    def test_equal_priced_tier_is_not_an_upgrade(self):
        table = TierTable("S", "X", "v1", (Tier(1, 10, 100), Tier(11, None, 100)))
        assert table.next_tier(5) is None


class TestSnapshotIdentity:
    def test_table_is_hashable_and_frozen(self, sugar):
        assert hash(sugar)
        with pytest.raises(Exception):
            sugar.version = "v2"  # type: ignore[misc]

    def test_version_is_carried(self, sugar):
        assert sugar.version == "2026-09-01"
