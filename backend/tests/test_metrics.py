"""Dashboard aggregation: an average day, never a total dressed up as one."""
import pandas as pd

from app.services.insights import generate_insights, whatsapp_summary
from app.services.metrics import (
    complete_days,
    daily_totals_by_weekday,
    heatmap_series,
    hourly_series,
    is_partial,
)


def frame(rows):
    return pd.DataFrame(rows, columns=["date", "hour", "footfall", "transactions", "sales"])


def day(date, hours, footfall=10, transactions=5, sales=500.0):
    return [(date, h, footfall, transactions, sales) for h in hours]


def by_hour(series):
    return {h["hour"]: h for h in series}


class TestHourlyAverages:
    def test_is_a_per_day_average_not_a_sum(self):
        df = frame(day("2026-09-14", [9], 10) + day("2026-09-15", [9], 20))
        h = by_hour(hourly_series(df))[9]
        assert h["footfall"] == 15  # not 30

    def test_conversion_comes_from_totals(self):
        # A quiet hour must not outweigh a busy one in the average.
        df = frame([("2026-09-14", 9, 2, 2, 100.0), ("2026-09-15", 9, 100, 10, 900.0)])
        assert by_hour(hourly_series(df))[9]["conversion"] == 12 / 102

    def test_an_unfinished_today_does_not_drag_the_evening_down(self):
        # 20:00 exists on the full day only, so it averages over one day.
        df = frame(
            day("2026-09-20", [9, 20], footfall=10) + day("2026-09-21", [9], footfall=10)
        )
        h = by_hour(hourly_series(df))
        assert h[20]["footfall"] == 10
        assert h[9]["footfall"] == 10

    def test_shops_are_added_before_averaging(self):
        df = frame([
            ("2026-09-14", 9, 10, 5, 500.0),  # shop A
            ("2026-09-14", 9, 30, 5, 500.0),  # shop B, same hour
            ("2026-09-15", 9, 20, 5, 500.0),
        ])
        assert by_hour(hourly_series(df))[9]["footfall"] == 30  # (40 + 20) / 2

    def test_closed_hours_are_zero(self):
        h = by_hour(hourly_series(frame(day("2026-09-14", [9]))))
        assert h[3]["footfall"] == 0 and h[3]["conversion"] == 0


class TestHeatmap:
    def test_weekday_averaged_over_its_own_occurrences(self):
        # Two Mondays and one Sunday: Monday must not look twice as busy.
        df = frame(
            day("2026-09-14", [9], 10)  # Mon
            + day("2026-09-21", [9], 10)  # Mon
            + day("2026-09-20", [9], 10)  # Sun
        )
        cells = {(c["dow"], c["hour"]): c["footfall"] for c in heatmap_series(df)}
        assert cells[(0, 9)] == cells[(6, 9)] == 10


class TestCompleteDays:
    week = sum((day(f"2026-09-{d:02d}", range(8, 22)) for d in range(14, 21)), [])

    def test_drops_a_final_day_that_stops_early(self):
        df = frame(self.week + day("2026-09-21", range(8, 15)))
        assert is_partial(df)
        assert "2026-09-21" not in set(complete_days(df)["date"])

    def test_keeps_a_final_day_that_ran_to_closing(self):
        df = frame(self.week + day("2026-09-21", range(8, 22)))
        assert not is_partial(df)

    def test_single_day_cannot_judge_itself_without_help(self):
        df = frame(day("2026-09-21", range(8, 15)))
        assert not is_partial(df)
        assert complete_days(df, partial_date="2026-09-21").empty

    def test_weekday_means_ignore_the_unfinished_day(self):
        df = frame(self.week + day("2026-09-21", range(8, 9)))  # Monday, one hour in
        means = daily_totals_by_weekday(df)
        assert means[0] == 14 * 10  # the full Monday, not averaged with 10


class TestInsightWording:
    def test_best_hour_ignores_a_single_visitor(self):
        rows = day("2026-09-21", [8], footfall=1, transactions=1)  # "100%"
        rows += day("2026-09-21", [9, 10], footfall=20, transactions=10)
        rows += day("2026-09-21", [11], footfall=20, transactions=8)
        texts = " ".join(i["text"] for i in generate_insights(frame(rows)))
        assert "100.0%" not in texts

    def test_one_person_is_singular(self):
        rows = day("2026-09-21", [9], footfall=10, transactions=2)
        rows += day("2026-09-21", [10], footfall=3, transactions=3)  # best, 3 visitors
        rows += [("2026-09-21", 11, 1, 1, 50.0)]
        texts = " ".join(i["text"] for i in generate_insights(frame(rows)))
        assert "1 people" not in texts

    def test_week_projection_only_from_several_complete_days(self):
        one = frame(day("2026-09-20", range(8, 22)))
        assert "a week" not in " ".join(i["text"] for i in generate_insights(one))
        assert "day like this" in " ".join(i["text"] for i in generate_insights(one))

    def test_a_partial_day_never_projects(self):
        df = frame(day("2026-09-21", range(8, 12)))
        texts = " ".join(i["text"] for i in generate_insights(df, "2026-09-21"))
        assert "so far" in texts and "a week" not in texts

    def test_multi_day_hours_say_average_day(self):
        df = frame(
            day("2026-09-14", [9], footfall=30, transactions=5)
            + day("2026-09-15", [9], footfall=30, transactions=5)
            + day("2026-09-14", [10], footfall=5, transactions=4)
            + day("2026-09-15", [10], footfall=5, transactions=4)
        )
        assert "on an average day" in " ".join(i["text"] for i in generate_insights(df))

    def test_whatsapp_uses_the_given_title(self):
        msg = whatsapp_summary(frame(day("2026-09-21", [9, 10])), "Summary for Mon 21 Sep so far")
        assert msg.splitlines()[0] == "📊 *Summary for Mon 21 Sep so far*"
        assert "Daily" not in msg
