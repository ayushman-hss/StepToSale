"""The demo shops must keep behaving like the businesses they represent.

These run the real generator with a fixed clock and check the properties the
demo's credibility rests on. Each one is a failure that actually happened:
a Rs4,165 perfume earning 27% of a kirana's sales, a station kiosk selling
paneer and detergent, and two different shops with near-identical takings.
"""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_bundle_sample as gen  # noqa: E402
from app.services.associations import (  # noqa: E402
    DEFAULT_MIN_LIFT,
    find_co_purchase_pairs,
    multi_item_baskets,
)

NOW = datetime(2026, 9, 21, 14, 30, tzinfo=gen.IST)
STAPLES = {"Foodgrains, Oil & Masala", "Cleaning & Household"}


@pytest.fixture(scope="module")
def shops():
    out = {}
    for code, profile in gen.STORES.items():
        gen.random.seed(42)
        lines = gen.generate_store(code, profile, NOW)
        catalog = pd.read_excel(gen.BASE / f"product_catalog_{code}.xlsx")
        lines = lines.merge(catalog[["sku", "category"]], on="sku")
        lines["value"] = lines["qty"] * lines["unit_price"]
        out[code] = lines
    return out


def per_bill(lines):
    return lines["value"].sum() / lines["transaction_id"].nunique()


def per_day(lines):
    return lines["value"].sum() / lines["date"].nunique()


class TestFormatsDiffer:
    def test_kiosk_bills_are_far_smaller(self, shops):
        assert per_bill(shops["S2"]) < 0.6 * per_bill(shops["S1"])

    def test_kirana_takes_clearly_more_per_day(self, shops):
        # Not two businesses that happen to land on the same number.
        assert per_day(shops["S1"]) > 1.4 * per_day(shops["S2"])

    def test_kiosk_rings_up_more_bills(self, shops):
        assert shops["S2"]["transaction_id"].nunique() > shops["S1"]["transaction_id"].nunique()

    def test_kirana_bills_hold_more_items(self, shops):
        items = {c: l.groupby("transaction_id").size().mean() for c, l in shops.items()}
        assert items["S1"] > items["S2"] + 0.5


class TestProductMix:
    @pytest.mark.parametrize("code", ["S1", "S2"])
    def test_no_single_product_dominates(self, shops, code):
        lines = shops[code]
        share = lines.groupby("sku")["value"].sum().max() / lines["value"].sum()
        assert share < 0.15

    def test_kirana_sells_mostly_staples(self, shops):
        by_cat = shops["S1"].groupby("category")["value"].sum()
        assert by_cat.idxmax() == "Foodgrains, Oil & Masala"

    def test_kiosk_barely_sells_staples(self, shops):
        lines = shops["S2"]
        share = lines[lines["category"].isin(STAPLES)]["value"].sum() / lines["value"].sum()
        assert share < 0.10

    def test_cheap_goods_outsell_expensive_ones(self, shops):
        units = shops["S1"].groupby("unit_price")["qty"].sum()
        cheap = units[units.index <= 50].sum()
        dear = units[units.index >= 500].sum()
        assert cheap > 3 * dear


class TestTimeAndToday:
    def test_history_ends_at_the_clock(self, shops):
        for lines in shops.values():
            today = lines[lines["date"] == NOW.date().isoformat()]
            assert not today.empty
            assert today["hour"].max() <= NOW.hour

    def test_twelve_weeks_of_history(self, shops):
        assert shops["S1"]["date"].nunique() == gen.WEEKS * 7 + 1


class TestBundlesStayMeaningful:
    @pytest.mark.parametrize("code,low,high", [("S1", 5, 20), ("S2", 1, 8)])
    def test_candidate_count_is_workable(self, shops, code, low, high):
        pairs = find_co_purchase_pairs(shops[code][["transaction_id", "sku"]])
        assert low <= len(pairs) <= high
        assert all(p["lift"] >= DEFAULT_MIN_LIFT for p in pairs)

    def test_support_counts_only_bills_that_can_hold_a_pair(self):
        lines = pd.DataFrame(
            {"transaction_id": ["a", "b", "b", "c", "c", "c"], "sku": ["x", "x", "y", "x", "y", "z"]}
        )
        assert multi_item_baskets(lines) == 2
