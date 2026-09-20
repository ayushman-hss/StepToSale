from fractions import Fraction

import pytest
from hypothesis import given, settings, strategies as st

from app.services.pooling.allocation import (
    MAX_SHAPLEY_MEMBERS,
    AllocationError,
    largest_remainder,
    pro_rata,
    shapley_allocation,
    shapley_values,
)


class TestLargestRemainder:
    @pytest.mark.parametrize(
        "total,weights,expected",
        [
            (100, [1, 1, 1], [34, 33, 33]),
            (10, [1, 1, 1], [4, 3, 3]),
            (1, [1, 1], [1, 0]),
            (0, [5, 5], [0, 0]),
            (7, [0, 3], [0, 7]),
            (100, [50, 50], [50, 50]),
            (75, [15, 20], [32, 43]),
            (5, [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]),
            (2, [1, 1, 1], [1, 1, 0]),
        ],
    )
    def test_known_splits(self, total, weights, expected):
        assert largest_remainder(total, weights) == expected

    def test_empty_weights_with_zero_total(self):
        assert largest_remainder(0, []) == []

    def test_empty_weights_with_money_to_split(self):
        with pytest.raises(AllocationError, match="zero parties"):
            largest_remainder(100, [])

    def test_all_zero_weights_with_money(self):
        with pytest.raises(AllocationError, match="every weight is zero"):
            largest_remainder(100, [0, 0])

    def test_all_zero_weights_without_money(self):
        assert largest_remainder(0, [0, 0]) == [0, 0]

    def test_negative_total(self):
        with pytest.raises(AllocationError, match="total must be >= 0"):
            largest_remainder(-1, [1])

    def test_negative_weight(self):
        with pytest.raises(AllocationError, match="weights must be >= 0"):
            largest_remainder(10, [5, -1])

    @pytest.mark.parametrize("bad", [1.5, "10", True])
    def test_non_int_total(self, bad):
        with pytest.raises(AllocationError):
            largest_remainder(bad, [1])

    def test_ties_break_deterministically(self):
        # Equal weights, one leftover paisa: it must always land on the first
        # party, not wherever dict ordering happens to put it.
        for _ in range(20):
            assert largest_remainder(10, [1, 1, 1]) == [4, 3, 3]

    def test_large_numbers(self):
        parts = largest_remainder(10**12 + 1, [1, 1, 1])
        assert sum(parts) == 10**12 + 1


class TestProRata:
    def test_splits_by_quantity(self):
        assert pro_rata(7500, {"S1": 15, "S2": 20}) == {"S1": 3214, "S2": 4286}

    def test_sums_exactly(self):
        out = pro_rata(7500, {"S1": 15, "S2": 20})
        assert sum(out.values()) == 7500

    def test_empty_membership(self):
        assert pro_rata(0, {}) == {}


def _game(values: dict[frozenset[str], int]):
    return lambda coalition: values.get(frozenset(coalition), 0)


class TestShapley:
    def test_symmetric_players_get_equal_shares(self):
        # Two identical stores contributing identically must split evenly.
        members = ["A", "B"]
        game = _game({frozenset({"A"}): 0, frozenset({"B"}): 0, frozenset({"A", "B"}): 100})
        assert shapley_allocation(members, game) == {"A": 50, "B": 50}

    def test_dummy_player_gets_nothing(self):
        # C never changes any coalition's value, so C must receive zero.
        members = ["A", "B", "C"]
        values = {}
        for subset in (
            {"A"}, {"B"}, {"C"}, {"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "B", "C"},
        ):
            base = 100 if {"A", "B"} <= subset else 0
            values[frozenset(subset)] = base
        out = shapley_allocation(members, _game(values))
        assert out["C"] == 0
        assert out["A"] == out["B"] == 50

    def test_efficiency_sums_to_grand_coalition(self):
        members = ["A", "B", "C"]
        values = {
            frozenset({"A"}): 10, frozenset({"B"}): 20, frozenset({"C"}): 30,
            frozenset({"A", "B"}): 50, frozenset({"A", "C"}): 60,
            frozenset({"B", "C"}): 70, frozenset({"A", "B", "C"}): 121,
        }
        out = shapley_allocation(members, _game(values))
        assert sum(out.values()) == 121

    def test_exact_values_are_fractions(self):
        members = ["A", "B", "C"]
        game = _game({frozenset({"A", "B", "C"}): 100})
        exact = shapley_values(members, game)
        assert all(isinstance(v, Fraction) for v in exact.values())
        assert sum(exact.values()) == 100
        # 100/3 does not divide evenly, so the exact value must stay fractional.
        assert exact["A"] == Fraction(100, 3)

    def test_rounding_still_sums_exactly(self):
        members = ["A", "B", "C"]
        game = _game({frozenset({"A", "B", "C"}): 100})
        out = shapley_allocation(members, game)
        assert sum(out.values()) == 100
        assert sorted(out.values()) == [33, 33, 34]

    def test_single_member(self):
        assert shapley_allocation(["A"], _game({frozenset({"A"}): 0})) == {"A": 0}

    def test_no_members(self):
        assert shapley_allocation([], _game({})) == {}

    def test_duplicate_members_rejected(self):
        with pytest.raises(AllocationError, match="distinct"):
            shapley_values(["A", "A"], _game({}))

    def test_empty_coalition_must_be_worthless(self):
        with pytest.raises(AllocationError, match="empty coalition"):
            shapley_values(["A"], lambda c: 5)

    def test_too_many_members_is_refused_clearly(self):
        members = [f"S{i}" for i in range(MAX_SHAPLEY_MEMBERS + 1)]
        with pytest.raises(AllocationError, match="use pro_rata"):
            shapley_values(members, _game({}))

    def test_at_the_member_cap_it_still_works(self):
        members = [f"S{i}" for i in range(MAX_SHAPLEY_MEMBERS)]
        game = _game({frozenset(members): 1200})
        out = shapley_allocation(members, game)
        assert sum(out.values()) == 1200


@given(
    total=st.integers(min_value=0, max_value=10**9),
    weights=st.lists(st.integers(min_value=0, max_value=10**6), min_size=1, max_size=25),
)
def test_largest_remainder_always_sums_exactly(total, weights):
    if sum(weights) == 0:
        if total:
            with pytest.raises(AllocationError):
                largest_remainder(total, weights)
        return
    parts = largest_remainder(total, weights)
    assert sum(parts) == total
    assert len(parts) == len(weights)
    assert all(p >= 0 for p in parts)


@given(
    total=st.integers(min_value=0, max_value=10**7),
    weights=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=15),
)
def test_largest_remainder_parts_track_weights(total, weights):
    parts = largest_remainder(total, weights)
    # A heavier weight can never receive strictly less than a lighter one.
    pairs = sorted(zip(weights, parts))
    for (w1, p1), (w2, p2) in zip(pairs, pairs[1:]):
        if w1 < w2:
            assert p1 <= p2


@settings(max_examples=50, deadline=None)
@given(
    grand=st.integers(min_value=0, max_value=10**6),
    n=st.integers(min_value=1, max_value=6),
)
def test_shapley_allocation_always_sums_to_grand(grand, n):
    members = [f"S{i}" for i in range(n)]
    game = _game({frozenset(members): grand})
    out = shapley_allocation(members, game)
    assert sum(out.values()) == grand


class TestRotation:
    def test_rotation_moves_the_leftover_unit(self):
        # 10 split three ways leaves one spare; it should not always land on
        # the same party across repeated settlements.
        winners = [largest_remainder(10, [1, 1, 1], r).index(4) for r in range(3)]
        assert winners == [0, 1, 2]

    def test_rotation_wraps(self):
        assert largest_remainder(10, [1, 1, 1], 3) == largest_remainder(10, [1, 1, 1], 0)

    def test_rotation_never_breaks_the_total(self):
        for r in range(10):
            assert sum(largest_remainder(100, [7, 11, 13], r)) == 100

    def test_rotation_cannot_override_a_genuine_ordering(self):
        # Rotation only decides ties; a clearly larger share still wins.
        for r in range(5):
            assert largest_remainder(10, [0, 100], r) == [0, 10]

    def test_negative_rotation_is_harmless(self):
        assert sum(largest_remainder(10, [1, 1, 1], -1)) == 10

    def test_pro_rata_accepts_rotation(self):
        a = pro_rata(10, {"A": 1, "B": 1, "C": 1}, 0)
        b = pro_rata(10, {"A": 1, "B": 1, "C": 1}, 1)
        assert sum(a.values()) == sum(b.values()) == 10
        assert a != b

    def test_shapley_accepts_rotation(self):
        members = ["A", "B", "C"]
        game = _game({frozenset(members): 100})
        a = shapley_allocation(members, game, 0)
        b = shapley_allocation(members, game, 1)
        assert sum(a.values()) == sum(b.values()) == 100
        assert a != b
