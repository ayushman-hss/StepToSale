import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.services.pooling import Pool, PoolError, PoolStatus, Strategy, Tier, TierTable


@pytest.fixture
def pool(sugar, rice):
    p = Pool("koramangala", "Koramangala Neighborhood Pool",
             {"SUGAR": sugar, "RICE": rice})
    p.open()
    return p


class TestLifecycle:
    def test_starts_as_draft(self, sugar):
        assert Pool("p", "P", {"SUGAR": sugar}).status is PoolStatus.DRAFT

    def test_happy_path(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.lock()
        assert pool.status is PoolStatus.LOCKED
        pool.settle()
        assert pool.status is PoolStatus.SETTLED

    def test_cannot_order_before_opening(self, sugar):
        p = Pool("p", "P", {"SUGAR": sugar})
        with pytest.raises(PoolError, match="orders need an open pool"):
            p.place_order("S1", "SUGAR", 10)

    def test_cannot_order_once_locked(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.lock()
        with pytest.raises(PoolError, match="orders need an open pool"):
            pool.place_order("S2", "SUGAR", 20)

    def test_cannot_withdraw_once_locked(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.lock()
        with pytest.raises(PoolError, match="cannot withdraw"):
            pool.withdraw("S1")

    def test_cannot_settle_twice(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.close()
        with pytest.raises(PoolError, match="lock it before settling"):
            pool.settle()

    def test_cannot_settle_without_locking(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        with pytest.raises(PoolError, match="lock it before settling"):
            pool.settle()

    def test_settled_is_terminal(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.close()
        for action in (pool.open, pool.lock, pool.cancel):
            with pytest.raises(PoolError, match="cannot go from settled"):
                action()

    def test_cancelled_is_terminal(self, pool):
        pool.cancel()
        for action in (pool.open, pool.lock):
            with pytest.raises(PoolError, match="cannot go from cancelled"):
                action()

    def test_cancelled_pool_cannot_be_projected(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.cancel()
        with pytest.raises(PoolError, match="nothing to settle"):
            pool.project()

    def test_unlock_reopens(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.lock()
        pool.unlock()
        assert pool.status is PoolStatus.OPEN
        pool.place_order("S2", "SUGAR", 20)

    def test_unlock_only_from_locked(self, pool):
        with pytest.raises(PoolError, match="cannot unlock an? ?open pool"):
            pool.unlock()

    def test_cannot_settle_an_empty_pool(self, pool):
        pool.lock()
        with pytest.raises(PoolError, match="no orders"):
            pool.settle()

    def test_close_rolls_back_the_lock_when_settlement_fails(self, pool):
        # An empty pool cannot settle; close() must not strand it in LOCKED.
        with pytest.raises(PoolError, match="no orders"):
            pool.close()
        assert pool.status is PoolStatus.OPEN


class TestOrders:
    @pytest.mark.parametrize("qty", [0, -1, -100])
    def test_quantity_must_be_positive(self, pool, qty):
        with pytest.raises(PoolError, match="qty must be >= 1"):
            pool.place_order("S1", "SUGAR", qty)

    @pytest.mark.parametrize("qty", [1.5, "10", True, None])
    def test_quantity_must_be_an_int(self, pool, qty):
        with pytest.raises(PoolError, match="qty must be an int"):
            pool.place_order("S1", "SUGAR", qty)

    def test_unknown_sku(self, pool):
        with pytest.raises(PoolError, match="no supplier price list"):
            pool.place_order("S1", "COFFEE", 10)

    def test_empty_store_code(self, pool):
        with pytest.raises(PoolError, match="store code"):
            pool.place_order("", "SUGAR", 10)

    def test_reordering_replaces_rather_than_accumulates(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S1", "SUGAR", 25)
        assert pool.qty_by_store("SUGAR") == {"S1": 25}

    def test_withdraw_one_line(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S1", "RICE", 10)
        pool.withdraw("S1", "SUGAR")
        assert pool.qty_by_store("SUGAR") == {}
        assert pool.qty_by_store("RICE") == {"S1": 10}

    def test_withdraw_whole_store(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S1", "RICE", 10)
        pool.withdraw("S1")
        assert pool.orders == {}

    def test_withdraw_nothing_to_withdraw(self, pool):
        with pytest.raises(PoolError, match="no matching order"):
            pool.withdraw("S9")

    def test_price_list_keyed_under_the_wrong_sku(self, sugar):
        with pytest.raises(PoolError, match="describes"):
            Pool("p", "P", {"RICE": sugar})


class TestSpecExample:
    """The worked example from the brief: S1 15kg, S2 20kg, sugar."""

    def test_alone_each_pays_the_top_price(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        s = pool.project(Strategy.UNIT_PRICE)
        p = s.products[0]
        assert p.pooled_unit_price == 4500
        assert p.total_savings == 0

    def test_pooled_reaches_the_middle_tier(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        p = pool.project().products[0]
        assert p.total_qty == 35
        assert p.pooled_unit_price == 4000
        assert p.tier_label == "20-49"
        assert p.invoice_total == 140_000
        # S1 alone 15*45 = 675, S2 alone 20*40 = 800 -> 1475 vs 1400 pooled.
        assert p.total_savings == 7_500

    def test_third_store_unlocks_the_cheapest_tier(self, pool):
        for store in ("S1", "S2", "S3"):
            pool.place_order(store, "SUGAR", 15 if store != "S2" else 20)
        p = pool.project().products[0]
        assert p.total_qty == 50
        assert p.pooled_unit_price == 3500
        assert p.tier_label == "50+"
        assert p.units_to_next_tier is None

    def test_unit_price_strategy_lets_a_big_store_save_nothing(self, pool):
        # S2 already qualifies for 40/kg alone, so a plain pooled unit price
        # hands all the benefit to S1. This is the unfairness Shapley fixes.
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        s = pool.project(Strategy.UNIT_PRICE)
        by_store = {x.store: x.savings for x in s.stores}
        assert by_store == {"S1": 7_500, "S2": 0}

    def test_shapley_splits_the_gain_evenly_between_two_needed_parties(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        s = pool.project(Strategy.SHAPLEY)
        by_store = {x.store: x.savings for x in s.stores}
        assert by_store == {"S1": 3_750, "S2": 3_750}

    def test_pro_rata_follows_quantity(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        s = pool.project(Strategy.PRO_RATA)
        by_store = {x.store: x.savings for x in s.stores}
        assert by_store == {"S1": 3_214, "S2": 4_286}
        assert sum(by_store.values()) == 7_500


class TestSettlementInvariants:
    @pytest.mark.parametrize("strategy", list(Strategy))
    def test_payables_match_the_supplier_invoice(self, pool, strategy):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        pool.place_order("S3", "RICE", 30)
        s = pool.project(strategy)
        assert sum(x.payable for x in s.stores) == s.invoice_total
        assert sum(x.savings for x in s.stores) == s.total_savings

    @pytest.mark.parametrize("strategy", list(Strategy))
    def test_no_store_pays_more_than_going_alone(self, pool, strategy):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        s = pool.project(strategy)
        assert all(x.payable <= x.cost_alone for x in s.stores)
        assert all(x.savings >= 0 for x in s.stores)

    def test_single_store_pool_saves_nothing(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        for strategy in Strategy:
            s = pool.project(strategy)
            assert s.total_savings == 0
            assert s.stores[0].savings == 0

    def test_pool_that_crosses_no_tier_saves_nothing(self, pool):
        # Both already in the cheapest tier; pooling changes nothing.
        pool.place_order("S1", "SUGAR", 60)
        pool.place_order("S2", "SUGAR", 70)
        s = pool.project(Strategy.SHAPLEY)
        assert s.total_savings == 0
        assert all(x.savings == 0 for x in s.stores)

    def test_flat_price_list_never_produces_savings(self, flat):
        p = Pool("p", "P", {"SALT": flat})
        p.open()
        p.place_order("S1", "SALT", 10)
        p.place_order("S2", "SALT", 90)
        assert p.project(Strategy.SHAPLEY).total_savings == 0

    def test_multi_product_totals_are_summed_per_store(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S1", "RICE", 10)
        pool.place_order("S2", "SUGAR", 20)
        pool.place_order("S2", "RICE", 20)
        s = pool.project(Strategy.PRO_RATA)
        assert len(s.products) == 2
        assert {p.sku for p in s.products} == {"RICE", "SUGAR"}
        s1 = next(x for x in s.stores if x.store == "S1")
        assert s1.cost_alone == 67_500 + 62_000
        assert s1.payable == s1.cost_alone - s1.savings

    def test_settlement_records_the_price_list_version(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        p = pool.project().products[0]
        assert p.price_list_version == "2026-09-01"
        assert p.supplier_id == "SUP1"

    def test_projection_does_not_mutate_the_pool(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        before = pool.orders
        pool.project(Strategy.SHAPLEY)
        assert pool.orders == before
        assert pool.status is PoolStatus.OPEN


class TestProgressHints:
    def test_reports_distance_to_the_next_tier(self, pool):
        pool.place_order("S1", "SUGAR", 15)
        pool.place_order("S2", "SUGAR", 20)
        p = pool.project().products[0]
        assert p.units_to_next_tier == 15
        assert p.next_tier_unit_price == 3500

    def test_top_tier_reports_no_further_gain(self, pool):
        pool.place_order("S1", "SUGAR", 80)
        p = pool.project().products[0]
        assert p.units_to_next_tier is None
        assert p.next_tier_unit_price is None


@settings(max_examples=120, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    quantities=st.lists(st.integers(min_value=1, max_value=200), min_size=1, max_size=6),
    strategy=st.sampled_from(list(Strategy)),
)
def test_settlement_always_balances(sugar, quantities, strategy):
    """Whatever the orders or the rule, the books must close exactly."""
    p = Pool("p", "P", {"SUGAR": sugar})
    p.open()
    for i, qty in enumerate(quantities):
        p.place_order(f"S{i}", "SUGAR", qty)

    s = p.project(strategy)
    product = s.products[0]

    assert sum(x.payable for x in s.stores) == s.invoice_total
    assert sum(x.savings for x in s.stores) == s.total_savings
    assert s.invoice_total == sugar.cost_for(sum(quantities))
    assert s.total_savings >= 0
    assert all(x.savings >= 0 for x in s.stores)
    assert all(x.payable >= 0 for x in s.stores)
    assert product.total_qty == sum(quantities)
    # Everything stays an exact integer number of paise.
    assert all(isinstance(x.payable, int) for x in s.stores)


class TestRotationFairness:
    def _weekly(self, sugar, weeks, strategy):
        totals: dict[str, int] = {}
        for week in range(weeks):
            p = Pool("p", "P", {"SUGAR": sugar}, rotation=week)
            p.open()
            p.place_order("S1", "SUGAR", 15)
            p.place_order("S2", "SUGAR", 20)
            p.place_order("S3", "SUGAR", 15)
            s = p.project(strategy)
            assert sum(x.savings for x in s.stores) == s.total_savings
            for x in s.stores:
                totals[x.store] = totals.get(x.store, 0) + x.savings
        return totals

    def test_symmetric_members_come_out_even_over_a_cycle(self, sugar):
        # S1 and S3 order identically. Without rotation S1 pockets the spare
        # paisa every single week; over one full cycle they must be equal.
        totals = self._weekly(sugar, 3, Strategy.SHAPLEY)
        assert totals["S1"] == totals["S3"]

    def test_default_rotation_is_still_deterministic(self, sugar):
        first = self._weekly(sugar, 1, Strategy.SHAPLEY)
        second = self._weekly(sugar, 1, Strategy.SHAPLEY)
        assert first == second

    def test_rotation_does_not_change_the_pool_total(self, sugar):
        for week in range(5):
            p = Pool("p", "P", {"SUGAR": sugar}, rotation=week)
            p.open()
            p.place_order("S1", "SUGAR", 15)
            p.place_order("S2", "SUGAR", 20)
            p.place_order("S3", "SUGAR", 15)
            s = p.project(Strategy.PRO_RATA)
            assert s.invoice_total == sugar.cost_for(50)
            assert sum(x.payable for x in s.stores) == s.invoice_total
